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

def remove_digits_from_string(string):
    return ''.join([i for i in string if not i.isdigit()])

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
    """
    Function to get all the parent-child relations together with the information about the objects from openBIS.
    This is a recursive function because the objects inside openBIS are like trees containing multiple
    relations with other objects.

    Parameters
    ----------
    selected_object : pybis.sample.Sample
        Selected openBIS object.
    parent_child_relationships : dict, optional
        Dictionary containing the openBIS objects and the relations between them. The default is None.

    Returns
    -------
    parent_child_relationships : TYPE
        Dictionary containing the openBIS objects and the relations between them.

    """
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

def convert_openbis_ontology(schema, openbis_ontology_map, mapped_schema = None):
    """
    Function to convert the openBIS names into names mapped in the context part of the JSON-LD file.
    It is a step necessary before creating the JSON-LD file.
    This function is recursive as there are many nodes inside the dictionary.

    Parameters
    ----------
    schema : dict
        Dictionary with all the information of the object that one wants to export.
    openbis_ontology_map : dict
        Dictionary to map openBIS property names into ontology names.
    mapped_schema : dict, optional
        Updated schema. The default is None.

    Returns
    -------
    mapped_schema : dict
        Updated schema.

    """
    if mapped_schema == None:
        mapped_schema = copy.deepcopy(schema)
    
    for key in schema:
        # Convert dictionary keys from openBIS names by ontology names
        if key in openbis_ontology_map:
            new_key = openbis_ontology_map[key]
            mapped_schema[new_key] = mapped_schema.pop(key)
        else:
            new_key = key
        
        # Convert properties with hasProperty in ontology column by a dictionary
        if "hasProperty" in new_key:
            new_key_split = new_key.split("-hasProperty-")
            first_property = new_key_split[0]
            second_property = new_key_split[1]
            mapped_schema[first_property] = {second_property: mapped_schema[new_key]}
            mapped_schema.pop(new_key)
        
        # Replace object codes by object relations using hasPart
        if "/" in new_key:
            new_key_split = new_key.split("/")
            object_code = new_key_split[-1]
            object_code = remove_digits_from_string(object_code) # Get openBIS object code
            
            old_key = new_key
            mapped_schema[old_key]["@type"] = openbis_ontology_map[object_code] # Add @type to the object
            
            new_key = f"hasPart-{old_key}"
            mapped_schema[new_key] = mapped_schema.pop(old_key) # Replace openBIS object path by hasPart relation
            
        if type(schema[key])==dict:
            convert_openbis_ontology(schema[key], openbis_ontology_map, mapped_schema[new_key])
    
    return mapped_schema

def merge_hasPart_dicts(schema):
    """
    Function to merge all the dictionaries related to hasPart keys into a list of dictionaries.

    Parameters
    ----------
    dictionary : dict
        Object schema.

    Returns
    -------
    merged_dicts : dict
        Schema with all hasPart properties merged into list of dictionaries.

    """
    merged_dicts = {}

    for key, value in schema.items():
        if isinstance(value, dict):
            # Recursively merge dictionaries in sublevels
            merged_value = merge_hasPart_dicts(value)
            if key.startswith("hasPart"):
                # Merge dictionaries with keys starting with "hasPart" into a list
                if "hasPart" not in merged_dicts:
                    merged_dicts["hasPart"] = []
                merged_dicts["hasPart"].append(merged_value)
            else:
                merged_dicts[key] = merged_value
        else:
            merged_dicts[key] = value

    return merged_dicts

#%% Import metadata schema
metadata_schema_filename = "Metadata Schema_version3.xlsx"
objects_metadata = pd.read_excel(metadata_schema_filename, sheet_name = "Metadata Schema")
objects_ontology = pd.read_excel(metadata_schema_filename, sheet_name = "Ontology - definition")

#%% openBIS parameter - Ontology converter
openbis_ontology_map = {}
for _, row in objects_metadata.iterrows():
    openbis_parameter = row["openBIS"]
    if is_nan(openbis_parameter) == False and is_nan(row["Ontology"]) == False:
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
        pass
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
selected_object_schema_converted = convert_openbis_ontology(selected_object_schema[openbis_selected_object_id], openbis_ontology_map)
selected_object_schema_for_jsonld = merge_hasPart_dicts(selected_object_schema_converted)
jsonld_schema["@graph"] = [selected_object_schema_for_jsonld]

#%% Export to JSON-LD
jsonld_object = json.dumps(jsonld_schema, indent=4)
 
# Writing to sample.json
with open("selected_object_schema.jsonld", "w") as outfile:
    outfile.write(jsonld_object)