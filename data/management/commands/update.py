import csv
import io
import os
import json
import glob
from bddl.activity import Conditions, get_all_activities, get_instance_count
from bddl.config import get_definition_filename
import tqdm
from data.utils import *
from data.models import *
from nltk.corpus import wordnet as wn
from django.db.utils import IntegrityError
from django.contrib.sites.models import Site
from django.core.files import File
from django.core.management.base import BaseCommand
from fs.zipfs import ZipFS
from typing import Set, Optional

class Command(BaseCommand):
    help = "generates all the Django objects using data from ig_pipeline, B1K google sheets, and bddl"


    def handle(self, *args, **options):
        self.preparation()
        self.create_synsets()
        self.create_category()
        self.create_objects()
        self.create_scenes()
        self.create_tasks()
        self.post_complete_operation()
    

    # =============================== helper functions ===============================
    def preparation(self):
        """
        put any preparation work (e.g. sanity check) here
        """
        print("Running preparation work...")
        # Update the site
        site = Site.objects.first()
        site.domain = "localhost:8000"
        site.save()

        # sanity check room types are up to date
        room_types_from_model = set([room_type for _, room_type in ROOM_TYPE_CHOICES])
        with open(f'{os.path.pardir}/bddl/bddl/generated_data/allowed_room_types.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            room_types_from_csv = set([row[0] for row in reader][1:])
        assert room_types_from_model == room_types_from_csv, "room types are not up to date with allowed_room_types.csv"

        # get object rename mapping
        self.object_rename_mapping = {}
        with open(f"{os.path.pardir}/ig_pipeline/metadata/object_renames.csv", newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                new_cat = row["New Category"].strip()
                obj_name = row["Object name"].strip()
                # sanity checks
                if obj_name != "":
                    assert len(obj_name.split('-')) == 2, f"{obj_name} should only have one \'-\'"
                    self.object_rename_mapping[obj_name] = f"{new_cat}-{obj_name.split('-')[1]}"


    def post_complete_operation(self):
        """
        put any post completion work (e.g. update stuff) here
        """
        print("Running post completion operations...")
        self.generate_synset_state()
        self.generate_object_images()


    def create_synsets(self):
        """
        create synsets with annotations from propagated_annots_canonical.json and hierarchy from output_hierarchy.json
        """
        def _generate_synset_hierarchy(synset_sub_hierarchy: Dict, parent: Optional[Synset], ancestors: Set[Synset], pbar):
            """
            helper function to generate synset hierarchy
            """
            synset_name = synset_sub_hierarchy["name"]
            synset_is_custom = wn_synset_exists(synset_name)  # TODO: use data from hierarchy. synset_sub_hierarchy["is_custom"] == "1"
            if synset_name != canonicalize(synset_name):
                print(f"synset {synset_name} is not canonicalized!")
            synset_definition = wn.synset(synset_name).definition() if wn_synset_exists(synset_name) else ""
            synset, created = Synset.objects.get_or_create(name=synset_name, defaults={"definition": synset_definition, "is_custom": synset_is_custom})
            if parent:
                synset.parents.add(parent)
            cur_ancestors = ancestors.copy()
            for ancestor in cur_ancestors:
                synset.ancestors.add(ancestor)
            cur_ancestors.add(synset)
            if created:
                for property_name in self.properties_data[synset_name]:
                    property_obj, _ = Property.objects.get_or_create(name=property_name)
                    synset.properties.add(property_obj)
                pbar.update()
            if "children" in synset_sub_hierarchy:
                for child_hierarchy in synset_sub_hierarchy["children"]:
                    _generate_synset_hierarchy(child_hierarchy, synset, cur_ancestors, pbar)

        print("Creating synsets...")   
        with open(rf"{os.path.pardir}/bddl/bddl/generated_data/propagated_annots_canonical.json", "r") as f:
            self.properties_data = json.load(f)     
        with open(rf"{os.path.pardir}/bddl/bddl/generated_data/output_hierarchy.json", "r") as f:
            synset_hierarchy = json.load(f)
            with tqdm.tqdm(total=len(self.properties_data)) as pbar:
                _generate_synset_hierarchy(synset_hierarchy, None, set(), pbar)


    def create_category(self):
        """
        create categories from object category mapping sheet
        """
        print("Creating categories...")        
        with open(f"{os.path.pardir}/bddl/bddl/generated_data/category_mapping.csv", newline='') as csvfile:
            n_categories = len(csvfile.readlines())
            csvfile.seek(0)
            reader = csv.DictReader(csvfile)
            for row in tqdm.tqdm(reader, total=n_categories):
                category_name = row["category"].strip()
                synset_name = row["synset"].strip()
                if not synset_name or not category_name:
                    print(f"Skipping problematic row: {row}")
                    continue
                synset_name = canonicalize(synset_name)
                synset, _ = Synset.objects.get_or_create(name=synset_name)
                try:
                    _ = Category.objects.create(name=category_name, synset=synset)
                except IntegrityError: 
                    raise Exception(f"duplicate entry {category_name} in object category mapping sheet!")
        

    def create_objects(self):
        """
        Create objects and map to categories (with object inventory)
        """
        print("Creating objects...")
        # first get Deletion Queue
        deletion_queue = set()
        with open(f"{os.path.pardir}/ig_pipeline/metadata/deletion_queue.csv", newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                deletion_queue.add(row["Object"].strip())
        # then create objects
        with open(f"{os.path.pardir}/ig_pipeline/artifacts/pipeline/object_inventory_future.json", "r") as f:
            for orig_name in tqdm.tqdm(json.load(f)["providers"].keys()):
                object_name = self.object_rename_mapping[orig_name] if orig_name in self.object_rename_mapping else orig_name
                if object_name not in deletion_queue:
                    category_name = object_name.split("-")[0]
                    category, _ = Category.objects.get_or_create(name=category_name)
                    object = Object.objects.create(name=object_name, original_name=orig_name, ready=False, category=category)
        with open(f"{os.path.pardir}/ig_pipeline/artifacts/pipeline/object_inventory.json", "r") as f:
            objs = []
            for object_name in tqdm.tqdm(json.load(f)["providers"].keys()):
                if object_name in self.object_rename_mapping:
                    object_name = self.object_rename_mapping[object_name]
                if object_name not in deletion_queue:
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
            for scene_name in tqdm.tqdm(planned_scene_dict):
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
                    for orig_name, count in planned_scene_dict[scene_name][room_name].items():
                        object_name = self.object_rename_mapping[orig_name] if orig_name in self.object_rename_mapping else orig_name
                        object, _ = Object.objects.get_or_create(name=object_name, defaults={
                            "original_name": orig_name,
                            "ready": False,
                            "planned": False, 
                            "category": Category.objects.get(name=object_name.split("-")[0])
                        })
                        RoomObject.objects.create(room=room, object=object, count=count)

        with open(rf"{os.path.pardir}/ig_pipeline/artifacts/pipeline/combined_room_object_list.json", "r") as f:
            current_scene_dict = json.load(f)["scenes"]
            for scene_name in tqdm.tqdm(current_scene_dict):
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
                    for orig_name, count in current_scene_dict[scene_name][room_name].items():
                        object_name = self.object_rename_mapping[orig_name] if orig_name in self.object_rename_mapping else orig_name
                        object, _ = Object.objects.get_or_create(name=object_name, defaults={
                            "original_name": orig_name,
                            "ready": False,
                            "planned": False,
                            "category": Category.objects.get(name=object_name.split("-")[0])
                        })
                        RoomObject.objects.create(room=room, object=object, count=count)


    def create_tasks(self):
        """
        create tasks and map to synsets
        """
        print("Creating tasks...")
        tasks = glob.glob(rf"{os.path.pardir}/bddl/bddl/activity_definitions/*")
        tasks = [(act, inst) for act in get_all_activities() for inst in range(get_instance_count(act))]
        for act, inst in tasks:
            # Load task definition
            conds = Conditions(act, inst, "omnigibson")
            synsets = set(synset for synset in conds.parsed_objects if synset != "agent.n.01")
            canonicalized_synsets = set(canonicalize(synset) for synset in synsets)
            with open(get_definition_filename(act, inst), "r") as f:
                raw_task_definition = "".join(f.readlines())

            # Create task object
            task_name = f"{act}-{inst}"
            task = Task.objects.create(name=task_name, definition=raw_task_definition)

            # add any synset that is not currently in the database
            for synset_name in canonicalized_synsets:
                is_used_as_non_substance, is_used_as_substance = object_substance_match(conds.parsed_initial_conditions + conds.parsed_goal_conditions, synset_name)
                is_used_as_fillable = object_used_as_fillable(conds.parsed_initial_conditions + conds.parsed_goal_conditions, synset_name)
                # all annotated synsets have been created before, so any newly created synset is illegal
                synset, _ = Synset.objects.get_or_create(name=synset_name)
                synset.is_used_as_substance = synset.is_used_as_substance or is_used_as_substance
                synset.is_used_as_non_substance = synset.is_used_as_non_substance or is_used_as_non_substance
                synset.is_used_as_fillable = synset.is_used_as_fillable or is_used_as_fillable
                synset.save()
                task.synsets.add(synset)
            task.save()

            # generate room requirements for task
            for cond in leaf_inroom_conds(conds.parsed_initial_conditions + conds.parsed_goal_conditions, synsets, task_name):
                assert len(cond) == 2, f"{task_name}: {str(cond)} not in correct format"
                # we don't check floor and wall because they are not in the room_object_list
                if cond[0] not in {"floor.n.01", "wall.n.01"}:
                    room_requirement, _ = RoomRequirement.objects.get_or_create(task=task, type=cond[1])
                    room_synset_requirements, created = RoomSynsetRequirement.objects.get_or_create(
                        room_requirement=room_requirement,
                        synset=Synset.objects.get(name=cond[0]),
                        defaults={"count": 1}
                    )
                    # if the requirement already occurred before, we increment the count by 1
                    if not created:
                        room_synset_requirements.count += 1
                        room_synset_requirements.save()


    def generate_synset_state(self):
        synsets = []
        substances = Property.objects.get(name="substance").synset_set.values_list("name", flat=True)
        for synset in tqdm.tqdm(Synset.objects.all()):
            if synset.name == "entity.n.01": synset.state = STATE_MATCHED   # root synset is always legal
            elif synset.name in substances:
                synset.state = STATE_SUBSTANCE
            elif synset.parents.count() > 0:
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
        with ZipFS(f"{os.path.pardir}/ig_pipeline/artifacts/pipeline/object_images.zip", write=False) as image_fs:
            for obj in tqdm.tqdm(Object.objects.all()):
                filename = f"{obj.original_name}.jpg"
                if not image_fs.exists(filename):
                    continue
                bio = io.BytesIO(image_fs.getbytes(filename))
                obj.photo = File(bio, name=filename)
                obj.save()
