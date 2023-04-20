import os
import csv
import glob 
import json
import pathlib
import yaml
import networkx as nx

from bddl.activity import Conditions
from collections import defaultdict
from nltk.corpus import wordnet as wn
from utils import *



def get_all_tasks():
    """
    Get a list of all defined tasks
    returns:
        task_to_fn: dict mapping task name to the file directory that contains the task definition
    """
    task_to_fn = {}  # task to filename mapping
    b1k_tasks = glob.glob(rf"{os.path.pardir}/ObjectPropertyAnnotation/init_goal_cond_annotations/problem_files_verified_b1k/*")
    b100_tasks = glob.glob(rf"{os.path.pardir}/bddl/bddl/activity_definitions/*")
    for x in sorted(b1k_tasks + b100_tasks):
        p = pathlib.Path(x)
        if not p.is_dir():
            continue
        act_name = p.name.replace(" ", "_").replace("-", "_").replace("'", "_")
        if act_name in task_to_fn:
            print(f"Found duplicate for {act_name}")
        task_to_fn[act_name] = p
    return task_to_fn


def get_scenes():
    """
    Get a list of defined and available scenes (and it's containing scene-objects)
    returns:
        scene_to_objects: dict mapping scene name to the object list that contains the scene definition
        available_scenes: list of available scenes
    """
    scene_to_objects = {}
    with open(rf"{os.path.pardir}/ig_pipeline/metadata/combined_room_object_list.json", "r") as f:
        scene_to_objects = json.load(f)["scenes"]
    with open("params.yaml", "r") as f:
        available_scenes = yaml.safe_load(f)["final_scenes"]
    available_scenes = [x.split('/')[-1] for x in available_scenes] # remove 'scene/' prefix
    return scene_to_objects, available_scenes


def get_objects_and_categories(scenes):
    """
    Get objects and categories and their correspondence
    returns:
        all_objects: list of all objects (planned) in the dataset
        cat_to_object: dict mapping category to list of available objects in that category
        provided_categories: set of categories that are provided by the dataset
        available_objects: list of available objects in the dataset
    """
    cat_to_object = defaultdict(list)
    with open(f"{os.path.pardir}/ig_pipeline/artifacts/pipeline/object_inventory.json", "r") as f:
        obj_json = json.load(f)
    available_objects = sorted(obj_json["providers"].keys())
    all_objects = sorted(obj_json["all"].keys())
    for obj in all_objects:
        cat_to_object[obj.split("-")[0]].append(obj)
    provided_categories = {x.split("-")[0] for x in all_objects}

    return all_objects, cat_to_object, provided_categories, available_objects


def get_all_synsets():
    """
    Build the synset graph that includes all wordnet and custom synsets
    returns:
        G: the synset graph
    """
    # Build the legit-synset graph
    G = nx.DiGraph()
    G.add_nodes_from(x.name() for x in wn.all_synsets())
    for parent in wn.all_synsets():
        for child in parent.hyponyms():
            G.add_edge(parent.name(), child.name())
            
    # Add the illegit-synset (custom) graph
    with open(f"{os.path.pardir}/ObjectPropertyAnnotation/object_property_annots/custom_synsets.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            child = row["custom_synset"].strip()
            parent = wn.synset(row["hypernyms"].strip()).name()
            assert parent in G.nodes, "Could not find " + parent
            G.add_edge(parent, child)
    return G


def get_task_synset_mapping(G, task_to_fn):
    """
    Get the mapping between task and its required synsets
    returns:
        task_to_synset: dict mapping task name to the required synsets
        sysnet_to_task: dict mapping synset to the tasks that require it
        task_to_scene_synset: dict mapping task name to the required scene objects
        task_to_non_scene_synset: dict mapping task name to the required non-scene objects
        task_required_synsets: set of all task-required synsets
        task_to_legal_synsets: set of task-required synsets that are in the synset graph
        task_to_illegal_synsets: set of task-rquired synsets that are not in the synset graph
        task_requirements: dict mapping task name to the required objects - room pair
    """
    legit_synsets = set(G.nodes)
    task_to_synset = {}
    task_to_scene_synset, task_to_non_scene_synset = {}, {}
    task_to_legal_synsets, task_to_illegal_synsets = {}, {}
    task_requirements = {}
    for task_name in task_to_fn:
        task_file = task_to_fn[task_name] / "problem0.bddl"
        assert task_file.exists(), f"{task_name} file missing"
        with open(task_file, "r") as f:
            predefined_problem = "".join(f.readlines())
        dom = "omnigibson" if "ObjectPropertyAnnotation" in str(task_file) else "igibson"
        conds = Conditions(task_name, "potato", dom, predefined_problem=predefined_problem)
        task_to_synset[task_name] = set(conds.parsed_objects.keys()) - {"agent.n.01"}
        raw_requirements = [cond[1:] for cond in conds.parsed_initial_conditions if cond[0] == "inroom"]
        assert all(len(req) == 2 for req in raw_requirements), task_name + ":" + str(raw_requirements)
        task_requirements[task_name] = sorted([(req.rsplit("_", 1)[0], rm) for req, rm in raw_requirements])
        task_to_scene_synset[task_name] = sorted([obj for obj, _ in task_requirements[task_name]])
        task_to_non_scene_synset[task_name] = sorted(task_to_synset[task_name] - set(task_to_scene_synset[task_name]))
        task_to_legal_synsets[task_name] = sorted(task_to_synset[task_name] & legit_synsets)
        task_to_illegal_synsets[task_name] = sorted(task_to_synset[task_name] - set(task_to_legal_synsets[task_name]))
    
    task_required_synsets = {x for s in task_to_synset.values() for x in s}
    synset_to_task = {s: sorted([t for t, ss in task_to_synset.items() if s in ss]) for s in sorted(task_required_synsets)}
    return task_to_synset, synset_to_task, task_to_scene_synset, task_to_non_scene_synset, task_to_legal_synsets, task_to_illegal_synsets, task_requirements


def get_category_synset_mapping(provided_categories):
    """
    Get the mapping between object catorgory and synset
    One synset can correspond to multiple categories
    returns:
        cat_to_synset: dict mapping category to corresponding synset
        synset_to_cat: dict mapping synset to corresponding category
    """
    # Get the category - synset mapping
    cat_to_synset = {}
    synset_to_cat = defaultdict(list)
    with open(f"{os.path.pardir}/category_mapping.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            category = row["category"].strip()
            synset = row["synset"].strip()
            if not synset or not category:
                print(f"Skipping problematic row: {row}")
                continue
            if category not in provided_categories:
                continue
            synset = canonicalize(synset)
            cat_to_synset[category] = synset
            synset_to_cat[synset].append(category)
    return cat_to_synset, synset_to_cat


def get_available_synsets(G, synset_to_cat, task_to_legal_synsets, cat_to_object):
    """
    Analyze whether task required synsets are available in the dataset
    returns:
        synset_to_objects: dict mapping synset to the objects that are available in the dataset
        task_to_found_synset: dict mapping task name to the synsets that has available objects in the dataset
        task_to_not_found_synset: dict mapping task name to the synsets that has no available objects in the dataset
    """
    found_synsets = set(synset_to_cat.keys())
    synset_to_objects = defaultdict(set)
    for s in {ss for value in task_to_legal_synsets.values() for ss in value}:
        # Get the tree of the synset
        child_synsets = [s] + list(nx.descendants(G, s))
        for cs in child_synsets:
            if cs in found_synsets:
                s_cats = synset_to_cat[cs]
                s_objs = {obj for cat in s_cats for obj in cat_to_object[cat]}
                synset_to_objects[s].update(s_objs)
        if s in synset_to_objects:
            synset_to_objects[s] = sorted(synset_to_objects[s])

    task_to_not_found_synset = {task_name: sorted(set(task_to_legal_synsets[task_name]) - set(synset_to_objects.keys())) for task_name in task_to_legal_synsets}
    task_to_found_synset = {task_name: sorted(set(task_to_legal_synsets[task_name]) - set(task_to_not_found_synset[task_name])) for task_name in task_to_legal_synsets}
    return synset_to_objects, task_to_found_synset, task_to_not_found_synset


def get_task_scene_mapping(G, task_to_fn, scene_to_objects, task_requirements):
    """
    For each task, find all scenes that compatible with it
    returns:
        task_to_scene: dict mapping task name to whether the scenes are compatible with it
    """
    task_to_scene = {}
    for task_name in task_to_fn:
        task_to_scene[task_name] = {"matched": [], "unmatched": {}}
        for scene in scene_to_objects:
            ret = scene_compatible_with_task(G, scene_to_objects, scene, task_requirements[task_name]) 
            if len(ret) == 0:
                task_to_scene[task_name]["matched"].append(scene)
            else:
                task_to_scene[task_name]["unmatched"][scene] = ret
    return task_to_scene
