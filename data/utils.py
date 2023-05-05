import csv
import os
import networkx as nx
from nltk.corpus import wordnet as wn
from typing import Tuple, List
from data.models import *


# STATE METADATA
STATE_MATCHED = "success"
STATE_PLANNED = "warning"
STATE_UNMATCHED = "danger"
STATE_SUBSTANCE = "info"
STATE_ILLEGAL = "secondary"
STATE_NONE = "light"


# predicates that indicates the presence of a substance in bddl
SUBSTANCE_PREDICATES = {"filled", "insource", "empty", "saturated", "contains", "covered"}
# predicates that can be used for both substance and non-substance
UNIVERSAL_PREDICATES = {"future", "real"}


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
            parent = wn.synset(row["hypernym"].strip()).name()
            assert parent in G.nodes, "Could not find " + parent
            G.add_edge(parent, child)
    return G


def canonicalize(s):
    try:
        return wn.synset(s).name()
    except:
        return s


def wn_synset_exists(synset):
  try:
    wn.synset(synset)
    return True
  except:
    return False


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


def object_substance_match(cond, object) -> Tuple[bool, bool]:
    """
    Return two bools corresponding to whether synset is used as a non-substance and as a substance, respectively, in this condition subtree
    """
    if not isinstance(cond, list):
        if cond == object.split('?')[-1]:
            return True, False
        else:
            return False, False
    if not isinstance(cond[0], list):
        if cond[0] in SUBSTANCE_PREDICATES:
            # in some bddl "covered" definitions, the substance is the 2nd one (reversed)
            if cond[0] == "covered" and ("stain.n.01" in cond[2] or "dust.n.01" in cond[2]):
                return (False, True) if cond[2] == object.split('?')[-1] else (True, False)
            elif cond[1] == object.split('?')[-1]:
                return False, True
        # if the predicate is universal, it can be used for both substance and non-substance, so we return False for both
        elif cond[0] in UNIVERSAL_PREDICATES:
            return False, False
    is_substance, is_non_substance = zip(*[object_substance_match(child, object) for child in cond])   
    return any(is_substance), any(is_non_substance)


def leaf_inroom_conds(cond) -> List[List[str]]:
    """
    Return a list of all inroom conditions in the subtree of cond
    """
    ret = []
    if isinstance(cond, list):
        for child in cond:
            ret.extend(leaf_inroom_conds(child))
        if cond[0] == "inroom":
            ret.append(cond)
    return ret    