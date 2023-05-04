import csv
import nltk
import os
import json
import glob
import gspread
import pathlib
from bddl.activity import Conditions
import tqdm
from data.utils import *
from data.models import *
from nltk.corpus import wordnet as wn
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.sites.models import Site
from django.core.files import File
from django.core.management.base import BaseCommand
from fs.zipfs import ZipFS

class Command(BaseCommand):
    help = "generates all the Django objects using data from ig_pipeline, B1K google sheets, and bddl"


    def handle(self, *args, **options):
        self.preparation()
        self.create_synsets(self.legal_synsets)
        self.create_objects()
        self.create_scenes()
        self.create_tasks(self.legal_synsets)
        self.post_complete_operation()
    

    # =============================== helper functions ===============================
    def preparation(self):
        """
        put any preparation work (e.g. sanity check) here
        """
        # Update the site
        site = Site.objects.first()
        site.domain = "localhost:8000"
        site.save()

        # install wordnet
        nltk.download('wordnet')
        # generate legal synsets
        self.G = get_synset_graph()
        self.legal_synsets = set(self.G.nodes)
        # sanity check room types are up to date
        room_types_from_model = set([room_type for _, room_type in ROOM_TYPE_CHOICES])
        with open(f'{os.path.pardir}/ig_pipeline/metadata/allowed_room_types.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            room_types_from_csv = set([row[0] for row in reader][1:])
        assert room_types_from_model == room_types_from_csv, "room types are not up to date with allowed_room_types.csv"

        # get object rename file
        gc = gspread.service_account(filename=os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
        worksheet = gc.open_by_key("10L8wjNDvr1XYMMHas4IYYP9ZK7TfQHu--Kzoi0qhAe4").worksheet("Object Renames")
        with open(f"{os.path.pardir}/object_renames.csv", 'w') as f:
            writer = csv.writer(f)
            writer.writerows(worksheet.get_all_values())
        self.object_rename_mapping = {}
        with open(f"{os.path.pardir}/object_renames.csv", newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                new_cat = row["New Category"].strip()
                obj_name = row["Object name"].strip()
                # sanity checks
                assert len(obj_name.split('-')) == 2, f"{obj_name} should only have one \'-\'"
                self.object_rename_mapping[obj_name] = f"{new_cat}-{obj_name.split('-')[1]}"


    def post_complete_operation(self):
        """
        put any post completion work (e.g. update stuff) here
        """
        self.generate_synset_hierarchy(self.G)
        self.generate_synset_state()
        self.generate_object_images()


    def create_synsets(self, legal_synsets):
        """
        create categories and synsets (with category_mappings.csv)
        """
        print("Creating synsets...")
        gc = gspread.service_account(filename=os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
        worksheet = gc.open_by_key("10L8wjNDvr1XYMMHas4IYYP9ZK7TfQHu--Kzoi0qhAe4").worksheet("Object Category Mapping")
        with open(f"{os.path.pardir}/category_mapping.csv", 'w') as f:
            writer = csv.writer(f)
            writer.writerows(worksheet.get_all_values())
        # get all annotated substances
        with open(rf"{os.path.pardir}/ObjectPropertyAnnotation/object_property_annots/properties_to_synsets.json", "r") as f:
            self.substances = json.load(f)["substance"]
        with open(f"{os.path.pardir}/category_mapping.csv", newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                category_name = row["category"].strip()
                synset_name = row["synset"].strip()
                if not synset_name or not category_name:
                    print(f"Skipping problematic row: {row}")
                    continue
                synset_name = canonicalize(synset_name)
                synset_definition = wn.synset(synset_name).definition() if wn_synset_exists(synset_name) else ""
                synset, _ = Synset.objects.get_or_create(
                    name=synset_name, 
                    defaults={
                        "definition": synset_definition, 
                        "legal": synset_name in legal_synsets,
                        "is_substance": synset_name in self.substances,
                    }
                )
                # safeguard to ensure every category only appears once in the csv file
                try:
                    _ = Category.objects.get_or_create(name=category_name, synset=synset)
                except IntegrityError:
                    raise Exception(f"{category_name} mapped to multiple synsets in category_mapping.csv!")

    def create_objects(self):
        """
        Create objects and map to categories (with object inventory)
        """
        print("Creating objects...")
        with open(f"{os.path.pardir}/ig_pipeline/artifacts/pipeline/object_inventory_future.json", "r") as f:
            for object_name in json.load(f)["providers"].keys():
                if object_name in self.object_rename_mapping:
                    object_name = self.object_rename_mapping[object_name]
                category_name = object_name.split("-")[0]
                category, _ = Category.objects.get_or_create(name=category_name)
                object = Object.objects.create(name=object_name, ready=False, category=category)
        with open(f"{os.path.pardir}/ig_pipeline/artifacts/pipeline/object_inventory.json", "r") as f:
            objs = []
            for object_name in json.load(f)["providers"].keys():
                if object_name in self.object_rename_mapping:
                    object_name = self.object_rename_mapping[object_name]
                category_name = object_name.split("-")[0]
                category, _ = Category.objects.get_or_create(name=category_name)
                # safeguard to ensure currently available objects are also in future planned dataset
                try:
                    object = Object.objects.get(name=object_name)
                except Object.DoesNotExist:
                    raise Exception(f"{object_name} in category {category}, which exists in object_inventory.json, is not in object_inventory_future.json!")
                object.ready = True
                objs.append(object)
            Object.objects.bulk_update(objs, ["ready"])

    def create_scenes(self):
        """
        create scene objects (which stores the room config)
        scene matching to tasks will be generated later when creating task objects
        """
        print("Creating scenes...")
        with open(rf"{os.path.pardir}/ig_pipeline/artifacts/pipeline/combined_room_object_list_future.json", "r") as f:
            planned_scene_dict = json.load(f)["scenes"]
            for scene_name in planned_scene_dict:
                scene, _ = Scene.objects.get_or_create(name=scene_name)
                for room_name in planned_scene_dict[scene_name]:
                    try:
                        room = Room.objects.create(
                            name=room_name, 
                            type=room_name.rsplit('_', 1)[0], 
                            ready=False, 
                            scene=scene
                        )
                    except IntegrityError:
                        raise Exception(f"room {room_name} in {scene.name} (not ready) already exists!")
                    for object_name, count in planned_scene_dict[scene_name][room_name].items():
                        if object_name in self.object_rename_mapping:
                            object_name = self.object_rename_mapping[object_name]
                        object, _ = Object.objects.get_or_create(name=object_name, defaults={
                            "ready": False,
                            "planned": False, 
                            "category": Category.objects.get(name=object_name.split("-")[0])
                        })
                        RoomObject.objects.create(room=room, object=object, count=count)

        with open(rf"{os.path.pardir}/ig_pipeline/artifacts/pipeline/combined_room_object_list.json", "r") as f:
            current_scene_dict = json.load(f)["scenes"]
            for scene_name in current_scene_dict:
                scene, _ = Scene.objects.get_or_create(name=scene_name)
                for room_name in current_scene_dict[scene_name]:
                    try:
                        room = Room.objects.create(
                            name=room_name, 
                            type=room_name.rsplit('_', 1)[0], 
                            ready=True, 
                            scene=scene
                        )
                    except IntegrityError:
                        raise Exception(f"room {room_name} in {scene.name} (ready) already exists!")
                    for object_name, count in current_scene_dict[scene_name][room_name].items():
                        if object_name in self.object_rename_mapping:
                            object_name = self.object_rename_mapping[object_name]
                        object, _ = Object.objects.get_or_create(name=object_name, defaults={
                            "ready": False,
                            "planned": False,
                            "category": Category.objects.get(name=object_name.split("-")[0])
                        })
                        RoomObject.objects.create(room=room, object=object, count=count)

    def create_tasks(self, legal_synsets):
        """
        create tasks and map to synsets
        """
        print("Creating tasks...")
        b1k_tasks = glob.glob(rf"{os.path.pardir}/ObjectPropertyAnnotation/init_goal_cond_annotations/problem_files_verified_b1k/*")
        b100_tasks = glob.glob(rf"{os.path.pardir}/bddl/bddl/activity_definitions/*")
        for filename in sorted(b1k_tasks + b100_tasks):
            task_filepath = pathlib.Path(filename)
            if not task_filepath.is_dir():
                continue
            task_file = task_filepath / "problem0.bddl"
            task_name = task_filepath.name.replace(" ", "_").replace("-", "_").replace("'", "_")
            assert task_file.exists(), f"{task_name} file missing"
            with open(task_file, "r") as f:
                predefined_problem = "".join(f.readlines())
            dom = "omnigibson" if "ObjectPropertyAnnotation" in str(task_file) else "igibson"
            conds = Conditions(task_name, "potato", dom, predefined_problem=predefined_problem)
            obj_to_synset = {obj: canonicalize(synset) for synset, objs in conds.parsed_objects.items() if synset != "agent.n.01" for obj in objs}
            task = Task.objects.create(name=task_name, definition=predefined_problem)
            # add any synset that is not currently in the database
            for object_name, synset_name in obj_to_synset.items():
                is_used_as_non_substance, is_used_as_substance = object_substance_match(conds.parsed_initial_conditions + conds.parsed_goal_conditions, object_name)
                synset, created = Synset.objects.get_or_create(
                    name=synset_name, 
                    defaults={
                        "definition": wn.synset(synset_name).definition() if wn_synset_exists(synset_name) else "",
                        "legal": synset_name in legal_synsets,
                        "is_substance": synset_name in self.substances,
                        "is_used_as_substance": is_used_as_substance,
                        "is_used_as_non_substance": is_used_as_non_substance
                    }
                )
                if not created:
                    synset.is_used_as_substance = True if is_used_as_substance else synset.is_used_as_substance
                    synset.is_used_as_non_substance = True if is_used_as_non_substance else synset.is_used_as_non_substance
                    synset.save()
                task.synsets.add(synset)
            task.save()

            # generate room requirements for task
            for cond in leaf_inroom_conds(conds.parsed_initial_conditions + conds.parsed_goal_conditions):
                assert len(cond[1:]) == 2, f"{task_name}: {str(cond[1:])} not in correct format"
                # we don't check floor and wall because they are not in the room_object_list
                if obj_to_synset[cond[1].split('?')[-1]] not in {"floor.n.01", "wall.n.01"}:
                    room_requirement, _ = RoomRequirement.objects.get_or_create(task=task, type=cond[2])
                    room_synset_requirements, created = RoomSynsetRequirement.objects.get_or_create(
                        room_requirement=room_requirement,
                        synset=Synset.objects.get(name=obj_to_synset[cond[1].split('?')[-1]]),
                        defaults={"count": 1}
                    )
                    # if the requirement already occurred before, we increment the count by 1
                    if not created:
                        room_synset_requirements.count += 1
                        room_synset_requirements.save()

    def generate_synset_hierarchy(self, G):
        """
        generate the parent/child and ancestor/descendent relationship for synsets
        """
        print("Generating synset hierarchy...")
        def _add_hypernyms_to_synset(G, synset: Synset):
            """Add all the hypernyms to G"""
            if G.has_node(synset.name):
                for synset_hypernym_name in G.predecessors(synset.name):
                    synset_hypernym, _ = Synset.objects.get_or_create(
                        name=synset_hypernym_name, 
                        defaults={
                            "definition": wn.synset(synset_hypernym_name).definition() if wn_synset_exists(synset_hypernym_name) else "",
                            "is_substance": False,  # we put False here because if it is a substance, it should have been added already
                            "legal": True
                        }
                    )
                    _add_hypernyms_to_synset(G, synset_hypernym)

        for synset in Synset.objects.all():
            _add_hypernyms_to_synset(G, synset)

        for synset_c in Synset.objects.all():
            if G.has_node(synset_c.name):
                for synset_p in Synset.objects.filter(name__in=G.predecessors(synset_c.name)):
                    synset_c.parents.add(synset_p)
                for synset_p in Synset.objects.filter(name__in=nx.ancestors(G, synset_c.name)):
                    synset_c.ancestors.add(synset_p)

    def generate_synset_state(self):
        synsets = []
        for synset in Synset.objects.all():
            if synset.is_substance:
                synset.state = STATE_SUBSTANCE
            elif synset.legal:
                if len(synset.matching_ready_objects) > 0:
                    synset.state = STATE_MATCHED
                elif len(synset.matching_objects) > 0:
                    synset.state = STATE_PLANNED
                else:
                    synset.state = STATE_UNMATCHED
            else:
                synset.state = STATE_ILLEGAL
            synsets.append(synset)
        Synset.objects.bulk_update(synsets, ["state"])

    def generate_object_images(self):
        print("Generating object images...")
        with ZipFS(f"{os.path.pardir}/ig_pipeline/artifacts/pipeline/object_images.zip", write=False) as image_fs:
            for obj in tqdm.tqdm(Object.objects.all()):
                filename = f"{obj.name}.jpg"
                if not image_fs.exists(filename):
                    continue
                bio = io.BytesIO(image_fs.getbytes(filename))
                obj.photo = File(bio, name=filename)
                obj.save()
