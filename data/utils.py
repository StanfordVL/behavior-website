import csv
import os
import networkx as nx
from nltk.corpus import wordnet as wn

from data.models import *


# STATE METADATA
STATE_MATCHED = "success"
STATE_PLANNED = "warning"
STATE_UNMATCHED = "danger"
STATE_SUBSTANCE = "info"
STATE_ILLEGAL = "secondary"
STATE_NONE = "light"


# predicates that indicates the presence of a substance in bddl
SUBSTANCE_PREDICATE = {"filled", "insource", "empty", "saturated", "contains", "covered"}


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
