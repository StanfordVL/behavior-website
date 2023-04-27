import os
import csv
import networkx as nx

from nltk.corpus import wordnet as wn

# STATE METADATA
STATE_MATCHED = "success"
STATE_PLANNED = "warning"
STATE_UNMATCHED = "danger"
STATE_SUBSTANCE = "info"
STATE_ILLEGAL = "secondary"

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
