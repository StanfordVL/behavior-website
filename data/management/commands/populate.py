import csv
import os
import json
import glob
import gspread
import pathlib
from bddl.activity import Conditions
from data.utils import get_synset_graph
from nltk.corpus import wordnet as wn

from data.models import *
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

SUBSTANCE_PREDICATE = {"filled", "insource", "empty", "saturated", "contains", "covered"}


class Command(BaseCommand):
    help = "generates all the Django objects using data from ig_pipeline, B1K google sheets, and bddl"


    def handle(self, *args, **options):
        G = get_synset_graph()
        legal_synsets = set(G.nodes)
        self.create_scenes()
        self.create_synsets(legal_synsets)
        self.create_objects()
        self.create_tasks(legal_synsets)
        self.generate_synset_hierarchy(G)
    

    # =============================== helper functions ===============================
    def create_scenes(self):
        """
        create scene objects (which stores the room config)
        scene matching to tasks will be generated later when creating task objects
        """
        with open(rf"{os.path.pardir}/ig_pipeline/artifacts/pipeline/combined_room_object_list_future.json", "r") as f:
            planned_scene_dict = json.load(f)["scenes"]
            for scene_name in planned_scene_dict:
                scene, _ = Scene.objects.get_or_create(name=scene_name)
                planned_room_config = json.dumps(planned_scene_dict[scene_name])
                for room_name in planned_room_config:
                    room = Room.objects.create(
                        name=room_name, 
                        type=room_name.rsplit('_', 1)[0], 
                        ready=False, 
                        scene=scene
                    )
                    for object_name, count in planned_room_config[room_name].items():
                        object = Object.objects.get(name=object_name)
                        RoomObject.objects.create(room=room, object=object, count=count)

        with open(rf"{os.path.pardir}/ig_pipeline/artifacts/pipeline/combined_room_object_list.json", "r") as f:
            current_scene_dict = json.load(f)["scenes"]
            for scene_name in current_scene_dict:
                scene, _ = Scene.objects.get_or_create(name=scene_name)
                current_room_config = json.dumps(current_scene_dict[scene_name])
                for room_name in current_room_config:
                    room = Room.objects.create(
                        name=room_name, 
                        type=room_name.rsplit('_', 1)[0], 
                        ready=True, 
                        scene=scene
                    )
                    for object_name, count in current_room_config[room_name].items():
                        object = Object.objects.get(name=object_name)
                        RoomObject.objects.create(room=room, object=object, count=count)



    def create_synsets(self, legal_synsets):
        """
        create categories and synsets (with category_mappings.csv)
        """
        gc = gspread.service_account(filename=os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
        worksheet = gc.open_by_key("10L8wjNDvr1XYMMHas4IYYP9ZK7TfQHu--Kzoi0qhAe4").worksheet("Object Category Mapping")
        with open(f"{os.path.pardir}/category_mapping.csv", 'w') as f:
            writer = csv.writer(f)
            writer.writerows(worksheet.get_all_values())
        with open(f"{os.path.pardir}/category_mapping.csv", newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                category_name = row["category"].strip()
                synset_name = row["synset"].strip()
                if not synset_name or not category_name:
                    print(f"Skipping problematic row: {row}")
                    continue
                synset_name = canonicalize(synset_name)
                synset_definition = wn.synset(synset_name).definition() if wn.synset(synset_name) else ""
                synset, _ = Synset.objects.get_or_create(
                    name=synset_name, 
                    definition=synset_definition,
                    legal=(synset_name in legal_synsets)
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
        with open(f"{os.path.pardir}/ig_pipeline/artifacts/pipeline/object_inventory_future.json", "r") as f:
            for object_name in json.load(f)["providers"].keys():
                category_name = object_name.split("-")[0]
                category, _ = Category.objects.get_or_create(name=category_name)
                object = Object.objects.create(name=object_name, ready=False, category=category)
        with open(f"{os.path.pardir}/ig_pipeline/artifacts/pipeline/object_inventory.json", "r") as f:
            for object_name in json.load(f)["providers"].keys():
                category_name = object_name.split("-")[0]
                category, _ = Category.objects.get_or_create(name=category_name)
                # safeguard to ensure currently available objects are also in future planned dataset
                try:
                    object = Object.objects.get(name=object_name, category=category)
                except ObjectDoesNotExist:
                    raise Exception(f"{object_name} in category {category}, which exists in object_inventory.json, is not in object_inventory_future.json!")
                object.ready = True
                object.save()


    def create_tasks(self, legal_synsets):
        """
        create tasks and map to synsets
        """
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
            synsets = set(conds.parsed_objects.keys()) - {"agent.n.01"}
            substances = set()
            obj_to_synset = {obj: synset for synset, objs in conds.parsed_objects.items() for obj in objs}
            task = Task(name=task_name)
            # check whether each synset is a substance
            for cond in conds.parsed_initial_conditions + conds.parsed_goal_conditions:
                if cond[0] in SUBSTANCE_PREDICATE:
                    # in some bddl "covered" definitions, the substance is the 2nd one (reversed)
                    try:
                        if cond[0] == "covered" and ("stain" in cond[2] or "dust" in cond[2]):
                            substances.add(obj_to_synset[cond[2]])
                        else:
                            substances.add(obj_to_synset[cond[1].split('?')[-1]])
                    except KeyError:
                        print(f"KeyError: {cond[1]} in task {task_name}, adding {cond[1].split('?')[-1]} to found_substances")
                        substances.add(cond[1].split('?')[-1])
            
                elif cond[0] == "inroom":
                    assert len(cond[1:]) == 2, f"{task_name}: {str(cond[1:])} not in correct format"
                    room_requirement = RoomRequirement.objects.get_or_create(task=task, room_type=cond[2])
                    room_synset_requirements, created = RoomSynsetRequirement.objects.get_or_create(
                        room_requirement=room_requirement,
                        synset=Synset.objects.get(name=obj_to_synset[cond[1].split('?')[-1]]),
                        defaults={"count": 1}
                    )
                    # if the requirement already occurred before, we increment the count by 1
                    if not created:
                        room_synset_requirements.count += 1
                        room_synset_requirements.save()

            for synset_name in synsets:
                synset, _ = Synset.objects.update_or_create(
                    name=synset_name, 
                    defaults={
                        "definition": wn.synset(synset_name).definition() if wn.synset(synset_name) else "",
                        "is_substance": synset_name in substances, 
                        "legal": synset_name in legal_synsets
                    }
                )
                task.synsets.add(synset)
            task.save()


    def generate_synset_hierarchy(self, G):
        """
        generate the parent-child relationship for synsets
        """
        for synset_c in Synset.objects.all():
            for synset_p in Synset.objects.all():
                if synset_c.legal and synset_p.legal:
                    if counts_for(G, synset_c, synset_p):
                        synset_p.children.add(synset_c)
                        synset_p.save()
            # add all its hypernyms to the synset objects
            self.add_hypernyms_to_synset(G, synset_c)

    
    def add_hypernyms_to_synset(self, G, synset):
        for synset_hypernym_name in G.predecessors(synset.name):
            synset_hypernym, _ = Synset.objects.get_or_create(
                name=synset_hypernym_name, 
                defaults={
                    "definition": wn.synset(synset_hypernym_name).definition() if wn.synset(synset_hypernym_name) else "",
                    "is_substance": False,  # we put False here because if it is a substance, it should have been added already
                    "legal": True
                }
            )
            # add parent-child relationship
            synset_hypernym.children.add(synset)
            synset_hypernym.save()
            if synset_hypernym_name != 'entity.n.01': # root hypernym
                self.add_hypernyms_to_synset(synset_hypernym)
