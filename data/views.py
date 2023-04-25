import csv
import os
import json
import glob
import gspread

from data.models import *
from django.shortcuts import render

SUBSTANCE_PREDICATE = {"filled", "insource", "empty", "saturated", "contains", "covered"}
G = get_synset_graph()
legal_synsets = set(G.nodes)

# 1. create scenes
def create_scenes():
    """
    create scene objects (which stores the room config)
    scene matching to tasks will be generated later when creating task objects
    """
    with open(rf"{os.path.pardir}/ig_pipeline/artifacts/pipeline/combined_room_object_list_future.json", "r") as f:
        planned_scene_dict = json.load(f)["scenes"]
        for scene_name in planned_scene_dict:
            planned_room_config = json.dumps(planned_scene_dict[scene_name])
            _, created = Scene.objects.update_or_create(
                name=scene_name, 
                ready=False, 
                defaults={'room_config': planned_room_config}
            )
            if created:
                print(f"Warning: overwritting room config for {scene_name}-planned!")
    with open(rf"{os.path.pardir}/ig_pipeline/artifacts/pipeline/combined_room_object_list.json", "r") as f:
        current_scene_dict = json.load(f)["scenes"]
        for scene_name in planned_scene_dict:
            current_room_config = json.dumps(current_scene_dict[scene_name])
            _ = Scene.objects.update_or_create(
                name=scene_name, 
                ready=True, 
                defaults={'room_config': current_room_config}
            )
            if created:
                print(f"Warning: overwritting room config for {scene_name}-current!")


def create_synsets():
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
            synset, _ = Synset.objects.get_or_create(name=synset_name, legal=(synset_name in legal_synsets))
            # Will raise IntegrityError if the category already maps to a different synset 
            # safeguard to ensure every category only appears once in the csv file
            _ = Category.objects.get_or_create(name=category_name, synset=synset)
            
   
def create_objects():
    """
    Create objects and map to categories (with object inventory)
    """
    with open(f"{os.path.pardir}/ig_pipeline/artifacts/pipeline/object_inventory_future.json", "r") as f:
        for object_name in json.load(f)["providers"].keys():
            category_name = obj.split("-")[0]
            category, _ = Category.objects.get_or_create(name=category_name)
            obj = Object.create(name=object_name, ready=False, category=category)
            obj.save()
    with open(f"{os.path.pardir}/ig_pipeline/artifacts/pipeline/object_inventory.json", "r") as f:
        for object_name in json.load(f)["providers"].keys():
            category_name = obj.split("-")[0]
            category, _ = Category.objects.get_or_create(name=category_name)
            # will raise DoesNotExist if no such object exists
            # safeguard to ensure currently available objects are also in future planned dataset
            object = Object.objects.get(name=object_name, category=category)
            object.ready = True
            object.save()


def create_tasks():
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
        room_requirements = []
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
                room_requirements.append([cond[1].rsplit("_", 1)[0], cond[2]])

        task.room_requirements = str(room_requirements)
        for synset_name in synsets:
            synset, _ = Synset.objects.update_or_create(
                name=synset_name, 
                defaults={"is_substance": synset_name in substances, "legal": synset_name in legal_synsets}
            )
            task.synsets.add(synset)
        task.save()


def generate_synset_hierarchy():
    """
    generate the parent-child relationship for synsets
    """
    for synset_c in Synset.objects.all():
        for synset_p in Synset.objects.all():
            if synset_c.legal and synset_p.legal:
                if counts_for(G, synset_c, synset_p):
                    synset_p.children.add(synset_c)
                    synset_p.save()
    


def index(request):
    return render(request, "data/index.html", {})

def tasks_list(request):
    return render(request, "data/index.html", {})

def synsets(request):
    return render(request, "data/index.html", {})