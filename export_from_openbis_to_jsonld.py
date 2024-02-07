# -*- coding: utf-8 -*-
"""
Created on Wed Feb  7 10:32:22 2024

@author: dafa
"""

#%% Import libraries
import pandas as pd
from pybis import Openbis
import json
import copy

#%% Functions
def is_nan(var):
    """Function to verify whether it is a NaN."""
    return var != var

def log_in(bisurl='openbis', bisuser='admin', bispasswd='changeit'):
    """Function to login to openBIS."""
    if Openbis(bisurl, verify_certificates=False).is_token_valid():
        session = Openbis(bisurl, verify_certificates=False)
    else:
        Openbis(bisurl, verify_certificates=False).login(bisuser, bispasswd, save_token=True)
        session = Openbis(bisurl, verify_certificates=False)
    return session

def get_parent_child_relationships_nested(selected_object, parent_child_relationships=None):
    if parent_child_relationships is None:
        parent_child_relationships = {}

    # Fetch parents of the current publication
    parents = selected_object.parents
    
    # Get selected object ID
    selected_object_id = selected_object.identifier

    if parents is not None:
        # Add current parents to the dictionary with child-parent relationships
        for parent_id in parents:
            parent = session.get_sample(parent_id)
            parent_child_relationships[selected_object_id][parent_id] = parent.props.all()
            get_parent_child_relationships_nested(parent, parent_child_relationships[selected_object_id])

    return parent_child_relationships

def convert_openbis_ontology(key, schema, openbis_ontology_map, mapped_schema = None):
    if mapped_schema == None:
        mapped_schema = copy.deepcopy(schema)
        
    for key in schema:
        if key in openbis_ontology_map:
            new_key = openbis_ontology_map[key]
            mapped_schema[new_key] = mapped_schema.pop(key)
        else:
            new_key = key
            
        if type(schema[key])==dict:
            convert_openbis_ontology(key, schema[key], openbis_ontology_map, mapped_schema[new_key])
    
    return mapped_schema

#%% Import metadata schema
metadata_schema_filename = "Metadata Schema_version3.xlsx"
objects_metadata = pd.read_excel(metadata_schema_filename, sheet_name = "Metadata Schema")
objects_ontology = pd.read_excel(metadata_schema_filename, sheet_name = "Ontology - definition")

#%% openBIS parameter - Ontology converter
openbis_ontology_map = {}
for _, row in objects_metadata.iterrows():
    openbis_parameter = row["openBIS"]
    if is_nan(openbis_parameter) == False and is_nan(row["Unit"]) == False:
        openbis_ontology_map[openbis_parameter] = row["Ontology"]

#%% Prepare @context for JSON-LD
jsonld_schema = {"@context": {"xsd": "http://www.w3.org/2001/XMLSchema#"}}
for _, row in objects_ontology.iterrows():
    entity_type = row["Type"]
    
    if entity_type == "id":
        entity_type = "@id"
    else:
        entity_type = f"xsd:{entity_type}"
    
    if is_nan(row["IRI"]):
        jsonld_schema["@context"][row["Entity"]] = {"@type": entity_type}
    else:
        jsonld_schema["@context"][row["Entity"]] = {"@id": row["IRI"], "@type": entity_type}

#%% openBIS connection
session = log_in(bisurl="localhost:8443/openbis", bisuser="admin", bispasswd="changeit")

#%% Select object
openbis_objects = session.get_samples() # See all the objects inside openBIS
openbis_selected_object_id = "/PUBLICATIONS/PUBLIC_REPOSITORIES/PUBL270"
openbis_selected_object = session.get_sample(openbis_selected_object_id)

#%% Collect all the information about the object from openBIS
parent_child_relationships = {openbis_selected_object_id: openbis_selected_object.props.all()}
selected_object_schema = get_parent_child_relationships_nested(openbis_selected_object, parent_child_relationships)

#%% Prepare data for JSON-LD
selected_object_schema_for_jsonld = convert_openbis_ontology(openbis_selected_object_id, selected_object_schema, openbis_ontology_map)
jsonld_schema["@graph"] = [selected_object_schema_for_jsonld]

#%% Export to JSON-LD
jsonld_object = json.dumps(jsonld_schema, indent=4)
 
# Writing to sample.json
with open("publication_schema.jsonld", "w") as outfile:
    outfile.write(jsonld_object)