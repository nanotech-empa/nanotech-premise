# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 11:32:36 2024

@author: dafa
"""

#%% Import libraries
import pandas as pd
from pybis import Openbis

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

#%% Import metadata schema
metadata_schema_filename = "Metadata_Schema_for_openBIS.xlsx"
objects_metadata = pd.read_excel(metadata_schema_filename, sheet_name = "Metadata Schema")
openbis_object_parameters = pd.read_excel(metadata_schema_filename, sheet_name = "openBIS - parameters")
openbis_vocabularies = pd.read_excel(metadata_schema_filename, sheet_name = "openBIS - vocabulary")
openbis_vocabulary_terms = pd.read_excel(metadata_schema_filename, sheet_name = "openBIS - vocabulary terms")

#%% Process metadata

# Vocabularies
openbis_vocabularies_terms = pd.merge(openbis_vocabularies, openbis_vocabulary_terms, on = "Vocabulary")
openbis_vocabularies_terms_groupby_term = openbis_vocabularies_terms.groupby("Vocabulary")

all_openbis_vocabularies = []

for _, openbis_vocabulary_terms_group in openbis_vocabularies_terms_groupby_term:
    openbis_vocabulary_terms_dict = {}
    openbis_vocabulary_terms_dict["code"] = openbis_vocabulary_terms_group["Vocabulary"].iloc[0]
    openbis_vocabulary_terms_dict["description"] = openbis_vocabulary_terms_group["Description"].iloc[0]
    openbis_vocabulary_terms_dict["terms"] = []
    
    # Vocabulary Terms
    for idx, term_code in enumerate(openbis_vocabulary_terms_group["Term code"]):
        term_label = openbis_vocabulary_terms_group["Term label"].iloc[idx]
        term_description = openbis_vocabulary_terms_group["Term description"].iloc[idx]
        openbis_vocabulary_terms_dict["terms"].append({"code": term_code,
                                                       "label": term_label,
                                                       "description": term_description})
    
    all_openbis_vocabularies.append(openbis_vocabulary_terms_dict)
    
# Property types
all_openbis_properties = []

for idx, openbis_property in openbis_object_parameters.iterrows():
    openbis_property_dict = {}
    openbis_property_dict["code"] = openbis_property["Code"]
    openbis_property_dict["label"] = openbis_property["Label"]
    openbis_property_dict["description"] = openbis_property["Description"]
    openbis_property_dict["dataType"] = openbis_property["DataType"]
    openbis_property_dict["managedInternally"] = openbis_property["managedInternally"]
    
    if is_nan(openbis_property["Vocabulary"]) == False:
        openbis_property_dict["vocabulary"] = openbis_property["Vocabulary"]
    
    if is_nan(openbis_property["Metadata"]) == False:
        openbis_property_dict["metaData"] = {"custom_widget": openbis_property["Metadata"]}
    
    all_openbis_properties.append(openbis_property_dict)

# Objects
all_openbis_objects = []
objects_metadata['ObjectID'] = objects_metadata['Metadata'].isna().cumsum()
objects_metadata_groups = objects_metadata.groupby('ObjectID')

for _, object_metadata_group in objects_metadata_groups:
    openbis_object_dict = {"sections": {"general_information": []}}
    object_metadata_group = object_metadata_group.reset_index()
    
    for idx, object_metadata in object_metadata_group.iterrows():
        if idx == 1:
            openbis_object_dict["code"] = object_metadata["openBIS datatype"]
            openbis_object_dict["generatedCodePrefix"] = object_metadata["openBIS"]
        if idx > 1:
            if is_nan(object_metadata["openBIS"]) == False:
                openbis_object_dict["sections"]["general_information"].append(object_metadata["openBIS"])
    
    all_openbis_objects.append(openbis_object_dict)

#%% Connect to openBIS
session = log_in(bisurl="localhost:8443/openbis", bisuser="admin", bispasswd="changeit")

#%% Create vocabularies, property types, and object types in openBIS

# Vocabularies
for openbis_vocabulary in all_openbis_vocabularies:
    try:
        session.new_vocabulary(**openbis_vocabulary).save()
    except ValueError:
        print(f"{openbis_vocabulary['code']} already exists.")

# Property types
already_openbis_properties = ["comments"]
for openbis_property in all_openbis_properties:
    if openbis_property["code"] not in already_openbis_properties:
        try:
            session.new_property_type(**openbis_property).save()
        except ValueError:
            print(f"{openbis_property['code']} already exists.")
    
# Object types
for openbis_object in all_openbis_objects:
    try:
        sections = openbis_object.pop('sections')
        object_type = session.new_object_type(autoGeneratedCode=True, 
                                              subcodeUnique=False,
                                              listable=True,
                                              showContainer=False,
                                              showParents=True,
                                              showParentMetadata=False,
                                              **openbis_object).save()
        for section, properties in sections.items():
            print(section, properties)
            for property_type in properties:
                object_type.assign_property(session.get_property_type(code=property_type))
                
    except ValueError:
        print(f"{openbis_object['code']} already exists.")