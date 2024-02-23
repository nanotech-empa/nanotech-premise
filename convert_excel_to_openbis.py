# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 13:49:43 2024

@author: dafa
"""

#%% Import libraries
import numpy as np
import pandas as pd
import json
import re

#%% Functions
def match_pattern(pattern, input_string):
    if re.match(pattern, input_string):
        return True
    else:
        return False

def get_all_relations(all_objects_relations, object_code_ontology_map, schema_ontology, all_objects_metadata, selected_object, context_jsonld = None, all_links_dict = None):
    if all_links_dict == None:
        first_selected_object = selected_object
        selected_object_processed = ''.join([i for i in selected_object if not i.isdigit()]) # Remove digits
        object_type = object_code_ontology_map[selected_object_processed]
        object_metadata = all_objects_metadata[object_type][all_objects_metadata[object_type]["ID"]==selected_object].to_dict('records')
        object_metadata = object_metadata[0]
        object_metadata.pop("ID", None)
        object_metadata["@type"] = object_type
        
        context_jsonld = {"xsd": "http://www.w3.org/2001/XMLSchema#"}
        all_links_dict = {selected_object: object_metadata}
    else:
        first_selected_object = None
        
    hasPartObjects = []
    for idx_col, column in all_objects_relations.loc[selected_object].items():
        if column == "hasPart":
            idx_col_processed = ''.join([i for i in idx_col if not i.isdigit()]) # Remove digits
            object_type = object_code_ontology_map[idx_col_processed]
            object_metadata = all_objects_metadata[object_type][all_objects_metadata[object_type]["ID"]==idx_col].to_dict('records')
            object_metadata = object_metadata[0]
            object_metadata.pop("ID", None)
            
            # Ontologise parameters
            for parameter in object_metadata:
                
                parameter_ontology = schema_ontology[schema_ontology["Entity"]==parameter]
                parameter_type = parameter_ontology["Type"].item()
                parameter_iri = parameter_ontology["IRI"].item()
                
                if is_nan(parameter_iri):
                    pass
                else:
                    parameter_is_relation = match_pattern(r'\w+(?:-\w+){2,}', parameter_iri)
                    if parameter_is_relation:
                        parameter_iri_split = parameter_iri.split("-")
                        parameter_dictionary = {}
                        current_dict = parameter_dictionary
                        for parameter in parameter_iri_split[:-1]:
                            current_dict[parameter] = {}
                            current_dict = current_dict[parameter]
                        current_dict[parameter_iri_split[-1]] = None
                        
                        #Do it at the end of the cycle (save parameters and dictionary and do it afterwards)
                        object_metadata[parameter] = parameter_dictionary
                    
                    if parameter_type == "id":
                        entity_type = "@id"
                    else:
                        entity_type = f"xsd:{parameter_type}"

                    context_jsonld[parameter] = {"@id": parameter_iri,
                                                 "@type": entity_type}
                    
                
            
            # Ontologise objects
            object_iri = schema_ontology[schema_ontology["Entity"]==object_type]["IRI"].item()
            if is_nan(object_iri):
                pass
            else:
                context_jsonld[object_type] = {"@id": object_iri,
                                               "@type": "@id"}
                
            object_metadata["@type"] = object_type
            all_links_dict[selected_object][idx_col] = object_metadata
            get_all_relations(all_objects_relations, object_code_ontology_map, schema_ontology, all_objects_metadata, idx_col, context_jsonld, all_links_dict[selected_object])
            
            hasPartObjects.append(object_metadata)
    
    if first_selected_object == selected_object:
        all_links_dict = {"@context": context_jsonld, "@graph": all_links_dict}
            
    return all_links_dict

def is_nan(var):
    """Function to verify whether it is a NaN."""
    return var != var

#%% Load excel datasheets
root_path = "C:\\Users\\dafa\\Documents\\git\\nanotech-premise"
metadata_openbis_schema_filename = f"{root_path}\\Metadata_Schema_for_openBIS.xlsx"
metadata_experiment_filename = f"{root_path}\\Metadata_Experiment_Objects.xlsx"

schema_metadata = pd.read_excel(metadata_openbis_schema_filename, sheet_name = "Metadata Schema")
schema_ontology = pd.read_excel(metadata_openbis_schema_filename, sheet_name = "Ontology - definition")

experiment_objects_excel = pd.ExcelFile(metadata_experiment_filename)
experiment_objects_excel_sheets_names = experiment_objects_excel.sheet_names

experiment_metadata = experiment_objects_excel.parse("Experiment")
experiment_metadata = experiment_metadata.fillna(method = "ffill")

#%% Develop maps
object_code_ontology_map = {}
for _, row in schema_metadata.iterrows():
    parameter_code = row["openBIS"]
    if is_nan(parameter_code) == False and is_nan(row["Ontology"]) == False and is_nan(row["Unit"]):
        object_code_ontology_map[parameter_code] = row["Ontology"]

#%% Process excel datasheets
all_objects_metadata = {}

for sheet_name in experiment_objects_excel_sheets_names:
    if sheet_name != "Experiment":
        objects_metadata = experiment_objects_excel.parse(sheet_name, dtype={'Work phone': str})
        for col_name, col in objects_metadata.items():
            if col.dtype == "datetime64[ns]":
                objects_metadata[col_name] = objects_metadata[col_name].astype(str)
        all_objects_metadata[sheet_name] = objects_metadata

all_unique_objects_ids = pd.unique(experiment_metadata[['Object 1', 'Object 2']].values.ravel('K'))
all_objects_relations = pd.DataFrame(0, index = all_unique_objects_ids, columns = all_unique_objects_ids)

for idx, object_1_id in enumerate(experiment_metadata["Object 1"]):
    object_2_id = experiment_metadata["Object 2"][idx]
    all_objects_relations.loc[object_1_id, object_2_id] = "hasPart"

selected_object = "PUBL1"
all_objects_relations_dict = get_all_relations(all_objects_relations, object_code_ontology_map, schema_ontology, all_objects_metadata, selected_object)

experiment_objects_excel.close()

#%% Export to JSON-LD
jsonld_object = json.dumps(all_objects_relations_dict, indent=4)
 
# Writing to sample.json
with open("selected_object_schema.jsonld", "w") as outfile:
    outfile.write(jsonld_object)
    

"""
Tasks:
    1 - Replace metadata names in experiment example by names given in the ontology excel datasheet
    2 - Link the JSON parameters and objects to the different entities (IRI)
    3 - Link the parameters to the units (meters, Volts, Amperes, etc.)
    4 - Link the parameters to the datatype
"""


