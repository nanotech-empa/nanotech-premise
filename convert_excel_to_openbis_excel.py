# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 14:34:11 2024

@author: dafa
"""

#%% Import libraries
import pandas as pd
from pybis import Openbis
import os
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


#%% Import metadata objects
root_path = "C:\\Users\\dafa\\Documents\\git\\nanotech-premise"
metadata_openbis_schema_filename = f"{root_path}\\Metadata_Schema_for_openBIS.xlsx"
metadata_experiment_filename = f"{root_path}\\Metadata_Experiment_Objects.xlsx"

# Get objects metadata schema
schema_metadata = pd.read_excel(metadata_openbis_schema_filename, sheet_name = "Metadata Schema")
# Get information concerning the ontologised parameters
schema_ontology = pd.read_excel(metadata_openbis_schema_filename, sheet_name = "Ontology - definition")

# Open the experiment example metadata Excel file
experiment_objects_excel = pd.ExcelFile(metadata_experiment_filename)
# Get all the datasheet names inside the Excel file
experiment_objects_excel_sheets_names = experiment_objects_excel.sheet_names

# Get the experiment example metadata from the Excel file
experiment_metadata = experiment_objects_excel.parse("Experiment")
# There are some objects that have more than one parent. In those cases the left column
# only has the code of object on the first relation and then it is empty for all the following ones.
# Therefore, this functions fill the rows with the first code.
experiment_metadata = experiment_metadata.fillna(method = "ffill")

#%% Process Excel datasheets
all_objects_metadata = {}

# Obtain metadata from all the objects from the multiple datasheets inside the Excel file
for sheet_name in experiment_objects_excel_sheets_names:
    if sheet_name != "Experiment":
        # One has to add here all the parameters that should not be read using default setup
        objects_metadata = experiment_objects_excel.parse(sheet_name, dtype={'Work phone': str})
        
        # Convert timestamp objects into strings
        for col_name, col in objects_metadata.items():
            if col.dtype == "datetime64[ns]":
                objects_metadata[col_name] = objects_metadata[col_name].astype(str)
        
        # Save the objects according to the type
        all_objects_metadata[sheet_name] = objects_metadata

# Generate matrix containing all the parent-child relations for all objects
all_unique_objects_ids = pd.unique(experiment_metadata[['Object 1', 'Object 2']].values.ravel('K'))
all_objects_relations = pd.DataFrame(0, index = all_unique_objects_ids, columns = all_unique_objects_ids)
for idx, object_1_id in enumerate(experiment_metadata["Object 1"]):
    relation_id = experiment_metadata["Relation"][idx]
    object_2_id = experiment_metadata["Object 2"][idx]
    all_objects_relations.loc[object_1_id, object_2_id] = relation_id

#%% Entity datasheet
openbis_entities_rows = []
openbis_entities_rows.append(["SAMPLE"])

for object_name in all_objects_metadata:
    object_eln_name = schema_metadata["openBIS datatype"][schema_metadata["Ontology"]==object_name].item()
    
    openbis_entities_rows.append(["Sample type"])
    openbis_entities_rows.append(object_eln_name)
    
    object_parameters = list(all_objects_metadata[object_name].keys())[1:] # Remove ID
    
    for index, parameter in enumerate(object_parameters):
        parameter_eln_name = schema_metadata["openBIS"][schema_metadata["Ontology"]==parameter].values[0]
        object_parameters[index] = parameter_eln_name
    
    object_eln_parameters = ["$", "Space", "Project", "Experiment", "Auto generate code", "Parents", "Children"]
    object_eln_parameters.extend(object_parameters)
    openbis_entities_rows.append(object_eln_parameters)
    
    for _, object_data in all_objects_metadata[object_name].iterrows():
        object_parameters_values = list(object_data.values)[1:]
        object_eln_parameters_values = ["","","","",True,"",""]
        object_eln_parameters_values.extend(object_parameters_values)
        openbis_entities_rows.append(object_eln_parameters_values)
    
#%% Close Excel object
experiment_objects_excel.close()
