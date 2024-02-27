# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 14:34:11 2024

@author: dafa
"""

#%% Import libraries
import pandas as pd
from pybis import Openbis
import os

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

#%% Create metadata openbis types sheet

openbis_types_excel_rows = []
version = 1

# Vocabularies
openbis_vocabularies_terms = pd.merge(openbis_vocabularies, openbis_vocabulary_terms, on = "Vocabulary")
openbis_vocabularies_terms_groupby_vocabulary = openbis_vocabularies_terms.groupby("Vocabulary")

for _, openbis_vocabulary_terms_group in openbis_vocabularies_terms_groupby_vocabulary:
    vocabulary_code = openbis_vocabulary_terms_group["Vocabulary"].iloc[0]
    vocabulary_description = openbis_vocabulary_terms_group["Description"].iloc[0]
    
    openbis_types_excel_rows.append(["VOCABULARY_TYPE"])
    openbis_types_excel_rows.append(["Version", "Code", "Description"])
    openbis_types_excel_rows.append([version, vocabulary_code, vocabulary_description])
    openbis_types_excel_rows.append(["Version", "Code", "Label", "Description"])
    
    # Vocabulary Terms
    for idx, term_code in enumerate(openbis_vocabulary_terms_group["Term code"]):
        term_label = openbis_vocabulary_terms_group["Term label"].iloc[idx]
        term_description = openbis_vocabulary_terms_group["Term description"].iloc[idx]
        openbis_types_excel_rows.append([version, term_code, term_label, term_description])
    
    openbis_types_excel_rows.append([])
    
# Property types
property_types_dictionary = {}
for idx, openbis_property in openbis_object_parameters.iterrows():
    if is_nan(openbis_property["Vocabulary"]) == False:
        property_vocabulary = openbis_property["Vocabulary"]
    else:
        property_vocabulary = ""
        
    if is_nan(openbis_property["Metadata"]) == False:
        property_metadata = {"custom_widget": openbis_property["Metadata"]}
    else:
        property_metadata = ""
        
    property_types_dictionary[openbis_property["Code"]] = [version, openbis_property["Code"], False, True, 
                                                           "General information", openbis_property["Label"],
                                                           openbis_property["DataType"], property_vocabulary, 
                                                           openbis_property["Description"], property_metadata, ""]

# Objects
objects_metadata['ObjectID'] = objects_metadata['Metadata'].isna().cumsum()
objects_metadata_groups = objects_metadata.groupby('ObjectID')

for _, object_metadata_group in objects_metadata_groups:
    openbis_types_excel_rows.append(["SAMPLE_TYPE"])
    openbis_types_excel_rows.append(["Version", "Code", "Description", "Auto generate codes", "Validation script", "Generated code prefix"])
    
    object_metadata_group = object_metadata_group.reset_index()
    
    for idx, object_metadata in object_metadata_group.iterrows():
        if idx == 1:
            openbis_types_excel_rows.append([version, object_metadata["openBIS datatype"], "", 
                                       True, "", object_metadata["openBIS"]])
            openbis_types_excel_rows.append(["Version", "Code", "Mandatory", "Show in edit views", "Section", "Property label",
                                       "Data type", "Vocabulary code", "Description", "Metadata", "Dynamic script"])
        if idx > 1:
            if is_nan(object_metadata["openBIS"]) == False:
                if object_metadata["openBIS"] == "$name":
                    openbis_types_excel_rows.append([version, "$name", False, True, "General information", "Name",
                                               "VARCHAR", "", "Name", ""])
                else:
                    openbis_types_excel_rows.append(property_types_dictionary[object_metadata["openBIS"]])
    
    openbis_types_excel_rows.append([])

#%% Convert from list of lists to Excel file
openbis_types_excel_dataframe = pd.DataFrame(openbis_types_excel_rows)
openbis_types_excel_filename = "Metadata_prepared_to_openBIS.xlsx"

if not os.path.exists(openbis_types_excel_filename):
    openbis_types_excel_dataframe.to_excel(openbis_types_excel_filename, "TYPES", header = False, index = False)
else:
    print("Excel file already exists! Change the script in case you want to create new sheets.")
