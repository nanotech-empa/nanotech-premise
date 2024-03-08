# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 15:57:14 2024

@author: dafa
"""

from rdflib import Graph
import json
from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
import networkx as nx
import matplotlib.pyplot as plt

filename = "C:\\Users\\dafa\\Documents\\git\\nanotech-premise\\selected_object_schema.json"
g = Graph()
result = g.parse(location=filename, format='json-ld')
v = g.serialize(destination=r'C:\\Users\\dafa\\Documents\\git\\nanotech-premise\\selected_object_schema.ttl', format='turtle')

G = rdflib_to_networkx_multidigraph(result)

# Plot Networkx instance of RDF Graph
pos = nx.spring_layout(G, scale=2)
edge_labels = nx.get_edge_attributes(G, 'r')
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
nx.draw(G, with_labels=True)

#if not in interactive mode for 
plt.show()