import collections
import re
import os
import csv
import json
import networkx as nx

from nltk.corpus import wordnet as wn
from data.models import Scene


def get_synset_graph():
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


def canonicalize(s):
    try:
        return wn.synset(s).name()
    except:
        return s
    

def counts_for(G, child, parent):  
    """Checks if child is a child of parent in the synset graph G"""
    try:
        if nx.has_path(G, parent, child):
            return True
        else:
            c = wn.synset(child).name()
            p = wn.synset(parent).name()
            return nx.has_path(G, p, c)
    except Exception as e:
        return False


def room_has_requirements(G, room_contents, room_reqs):
    """Check whether a room contains all the required room-objects"""
    for req_name, req_number in room_reqs.items():
        found_stuff_for_req = 0
        for content_name, content_cnt in room_contents.items():
            if counts_for(G, content_name, req_name):
                found_stuff_for_req += content_cnt
                
        if found_stuff_for_req < req_number:
            return f"contains {found_stuff_for_req} {req_name} while {req_number} is required"
    return ""


def any_room_has_requirements(G, scene_contents, required_rm, required_stuff):
    """Check whether any room in a scene contains the required room-objects"""
    output = ""
    matching_scene_rooms = [x for x in scene_contents.keys() if re.fullmatch("^" + required_rm + "_[0-9]+$", x)]
    if len(matching_scene_rooms) == 0:
        return f" no {required_rm} found in scene;"
    for msr in matching_scene_rooms:
        ret = room_has_requirements(G, scene_contents[msr], required_stuff)
        if len(ret) == 0:
            return ""
        else:
            output += f" {msr} {ret};"
    return output
            

def scene_compatible_with_task(G, scene_contents: str, task_requirements: str):
    """Check whether a scene is compatible with a task (i.e. contains all the scene-required room-objects)"""
    requirements_by_rm = collections.defaultdict(collections.Counter)
    for obj, rm in json.loads(task_requirements):
        assert not rm.endswith("_0")
        requirements_by_rm[rm.replace("_0", "")][obj] += 1
    
    for required_rm, required_stuff in requirements_by_rm.items():
        ret = any_room_has_requirements(G, json.loads(scene_contents), required_rm, required_stuff)
        if len(ret) > 0:
            return f"No matching {required_rm}:{ret[:-1]}."
    return ""
