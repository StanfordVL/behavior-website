import csv
import os
import networkx as nx
from nltk.corpus import wordnet as wn
from typing import Tuple, List, Set
from data.models import *

# STATE METADATA
STATE_MATCHED = "success"
STATE_PLANNED = "warning"
STATE_UNMATCHED = "danger"
STATE_SUBSTANCE = "info"
STATE_ILLEGAL = "secondary"
STATE_NONE = "light"


# predicates that can only be used for substances
SUBSTANCE_PREDICATES = {"filled", "insource", "empty", "saturated", "contains", "covered"}
# predicates that can only be used for non-substances
NON_SUBSTANCE_PREDICATES = {
    "cooked", "frozen", "closed", "open", "folded", "unfolded", "toggled_on", "hot", "on_fire", "assembled",
    "broken", "ontop", "nextto", "under", "touching", "inside", "overlaid", "attached", "draped", "inroom"
}
# predicates that indicate the need for a fillable volume
FILLABLE_PREDICATES = {"filled", "contains", "empty"}


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
            assert parent in G.nodes, f"Could not find {parent}"
            assert child not in G.nodes, f"Custom synset {child} already in wordnet!"
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


def object_substance_match(cond, synset) -> Tuple[bool, bool]:
    """
    Return two bools corresponding to whether synset is used as a non-substance and as a substance, respectively, in this condition subtree
    """
    if not isinstance(cond, list):
        if cond.split('?')[-1].rsplit('_', 1)[0] == synset:
            return True, False
        else:
            return False, False
    elif not isinstance(cond[0], list):
        if cond[0] in SUBSTANCE_PREDICATES:
            if cond[1].split('?')[-1].rsplit('_', 1)[0] == synset:  # non-substance
                return True, False
            elif cond[2].split('?')[-1].rsplit('_', 1)[0] == synset: # substance
                return False, True
            else:
                return False, False
        # if the predicate is universal, it can be used for both substance and non-substance, so we return False for both
        elif cond[0] in NON_SUBSTANCE_PREDICATES and \
            (cond[1].split('?')[-1].rsplit('_', 1)[0] == synset or (len(cond) == 3 and cond[2].split('?')[-1].rsplit('_', 1)[0] == synset)):
            return True, False
        else:
            return False, False
    else:
        is_substance, is_non_substance = zip(*[object_substance_match(child, synset) for child in cond])   
    return any(is_substance), any(is_non_substance)


def object_used_as_fillable(cond, synset) -> Tuple[bool, bool]:
    """
    Return a bool corresponding to whether the synset is used as a fillable at any point
    """
    if not isinstance(cond, list):
        return False
    elif not isinstance(cond[0], list):
        if cond[0] in FILLABLE_PREDICATES:
            return cond[1].split('?')[-1].rsplit('_', 1)[0] == synset
        else:
            return False
    else:
        return any([object_used_as_fillable(child, synset) for child in cond])   


def leaf_inroom_conds(cond, synsets: Set[str], task_name: str) -> List[Tuple[str, str]]:
    """
    Return a list of all inroom conditions in the subtree of cond
    """
    ret = []
    if isinstance(cond, list):
        for child in cond:
            ret.extend(leaf_inroom_conds(child, synsets, task_name))
        if cond[0] == "inroom":
            synset = cond[1].split('?')[-1].rsplit("_", 1)[0]
            assert synset in synsets, f"{task_name}: {synset} not in valid format"
            ret.append((canonicalize(synset), cond[2]))
    return ret    