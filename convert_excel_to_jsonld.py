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

def get_object_metadata(all_objects_metadata, selected_object):
    """
    Obtain and process object metadata

    Parameters
    ----------
    all_objects_metadata : TYPE
        DESCRIPTION.
    selected_object : TYPE
        DESCRIPTION.

    Returns
    -------
    object_metadata : TYPE
        DESCRIPTION.

    """
    # Remove digits
    object_code = ''.join([i for i in selected_object if not i.isdigit()])
    
    # Obtain the object_type from object code
    object_type = object_code_ontology_map[object_code]
    
    # Obtain the object metadata
    object_metadata = all_objects_metadata[object_type][all_objects_metadata[object_type]["ID"] == selected_object].to_dict('records')
    object_metadata = object_metadata[0]
    object_metadata.pop("ID", None)
    
    return object_metadata, object_type

def get_parameter_context(parameter_type):
    """
    Get the parameter datatype

    Parameters
    ----------
    parameter_type : TYPE
        DESCRIPTION.

    Returns
    -------
    entity_type : TYPE
        DESCRIPTION.

    """
    
    if parameter_type == "id":
        entity_type = "@id"
    else:
        entity_type = f"xsd:{parameter_type}"
    
    return entity_type

def process_object_metadata(object_type, object_metadata, schema_ontology, context_jsonld):
    """
    Ontologise all the parameters inside each object

    Parameters
    ----------
    object_type : TYPE
        DESCRIPTION.
    object_metadata : TYPE
        DESCRIPTION.
    schema_ontology : TYPE
        DESCRIPTION.
    context_jsonld : TYPE
        DESCRIPTION.

    Returns
    -------
    object_metadata : TYPE
        DESCRIPTION.
    context_jsonld : TYPE
        DESCRIPTION.

    """
    # Ontologise parameters
    relation_parameters = {}
    for parameter in object_metadata:
        
        if is_nan(object_metadata[parameter]):
            object_metadata[parameter] = None
        
        # Get parameter IRI and type
        parameter_ontology = schema_ontology[schema_ontology["Entity"]==parameter]
        parameter_type = parameter_ontology["Type"].item()
        parameter_iri = parameter_ontology["IRI"].item()
        
        # If the parameter is not linked to some ontology, ignore it.
        if is_nan(parameter_iri):
            pass
        else:
            # Verify whether the parameter is mapped using a relation between different entities
            parameter_is_relation = match_pattern(r'\w+(?:-\w+){2,}', parameter_iri)
            
            # If the parameter is a relation between different entities, one needs to map all the entities
            # and convert the IRI into a dictionary of dictionaries representing the relations
            
            if parameter_is_relation:
                # Split the IRI into the different parameters
                parameter_iri_split = parameter_iri.split("-")
                parameter_dictionary = {}
                current_dict = parameter_dictionary
                
                # Convert the parameter into a dictionary of dictionaries
                for sub_parameter in parameter_iri_split[:-1]:
                    current_dict[sub_parameter] = {}
                    current_dict = current_dict[sub_parameter]
                    
                    # Verify whether the parameters comprising the relation are mapped
                    sub_parameter_ontology = schema_ontology[schema_ontology["Entity"]==sub_parameter]
                    sub_parameter_type = sub_parameter_ontology["Type"].item()
                    sub_parameter_iri = sub_parameter_ontology["IRI"].item()
                    
                    # If the parameter is not mapped, do not add it to the @context
                    if is_nan(sub_parameter_iri):
                        pass
                    else:
                        # Map the tags according to the JSON-LD standards and
                        # add the mapped parameter to the @context of the JSON-LD file
                        entity_type = get_parameter_context(sub_parameter_type)
                        context_jsonld[sub_parameter] = {"@id": sub_parameter_iri,
                                                         "@type": entity_type}
                
                # Add the last level of the parameter with relations
                current_dict[parameter_iri_split[-1]] = object_metadata[parameter]
                
                # Save the information to add after finishing the cycle
                relation_parameters[parameter] = parameter_dictionary
            else:
                # Map the tags according to the JSON-LD standards and
                # add the mapped parameter to the @context of the JSON-LD file
                entity_type = get_parameter_context(parameter_type)
                context_jsonld[parameter] = {"@id": parameter_iri,
                                             "@type": entity_type}
    
    # Replace the initial parameter by the mapped one
    for parameter in relation_parameters:
        relation_parameters_first_keys = relation_parameters[parameter].keys()
        relation_parameters_first_keys = list(relation_parameters_first_keys)
        relation_parameter_first_key = relation_parameters_first_keys[0]
        # Get the first level parameter of the entire parameter-relation-parameter
        object_metadata[relation_parameter_first_key] = relation_parameters[parameter][relation_parameter_first_key]
        # Remove the initial parameter
        object_metadata.pop(parameter)
            
    # Ontologise objects (map it only if there is an IRI in the list)
    object_iri = schema_ontology[schema_ontology["Entity"]==object_type]["IRI"].item()
    if is_nan(object_iri):
        pass
    else:
        context_jsonld[object_type] = {"@id": object_iri,
                                       "@type": "@id"}
        
    object_metadata["@type"] = object_type
    
    return object_metadata, context_jsonld

def match_pattern(pattern, input_string):
    """
    Verify whether the input_string follows the given pattern

    Parameters
    ----------
    pattern : TYPE
        DESCRIPTION.
    input_string : TYPE
        DESCRIPTION.

    Returns
    -------
    bool
        DESCRIPTION.

    """
    if re.match(pattern, input_string):
        return True
    else:
        return False

def compute_jsonld_data(all_objects_relations, object_code_ontology_map, schema_ontology, all_objects_metadata, selected_object, context_jsonld = None, all_links_dict = None):
    
    # At the beginning, the selected object is added to the dictionary that is going to be used
    # to generate the JSON-LD file
    if all_links_dict == None:
        # Save the selected object because it is needed at the end of the recursive function to
        # save the context and graph into one single dictionary
        first_selected_object = selected_object
        
        # Obtain object metadata and object type
        object_metadata, object_type = get_object_metadata(all_objects_metadata, selected_object)
        
        # Generate JSON-LD context
        context_jsonld = {"xsd": "http://www.w3.org/2001/XMLSchema#"}
        
        # Ontologise object metadata according to the pre-generated Excel datasheet and 
        # add more details to the JSON-LD context
        object_metadata, context_jsonld = process_object_metadata(object_type, object_metadata, schema_ontology, context_jsonld)
        
        # Generate JSON-LD graph
        all_links_dict = {selected_object: object_metadata}
    else:
        first_selected_object = None
        
    for idx_col, column in all_objects_relations.loc[selected_object].items():
        
        # Only map the objects that are parents of the selected object
        if column != 0:
            # Obtain object metadata and object type
            object_metadata, object_type = get_object_metadata(all_objects_metadata, idx_col)
            
            # Ontologise object metadata according to the pre-generated Excel datasheet and 
            # add more details to the JSON-LD context
            object_metadata, context_jsonld = process_object_metadata(object_type, object_metadata, schema_ontology, context_jsonld)
            
            # Add relation to the JSON-LD context
            # Ontologise relations (map it only if there is an IRI in the list)
            relation_ontology = schema_ontology[schema_ontology["Entity"] == column]
            relation_iri = relation_ontology["IRI"].item()
            if is_nan(relation_iri):
                pass
            else:
                context_jsonld[column] = {"@id": relation_iri,
                                               "@type": "@id"}
                
            object_metadata["parent-child relation"] = column
            
            # Save metadata into the JSON-LD graph
            all_links_dict[selected_object][idx_col] = object_metadata
            
            # Obtain the metadata until the last object level
            compute_jsonld_data(all_objects_relations, object_code_ontology_map, schema_ontology, all_objects_metadata, idx_col, context_jsonld, all_links_dict[selected_object])
            
            
    # When the recursive function finishes, save the context and the graph into one unique dictionary
    # that is going to be used to generate the JSON-LD
    if first_selected_object == selected_object:
        all_links_dict = {"@context": context_jsonld, "@graph": all_links_dict}
            
    return all_links_dict

def is_nan(var):
    """Function to verify whether it is a NaN."""
    return var != var

def merge_relations(d):
    """
    Function to merge the objects which has the same relation within the same level of depth into a list of objects

    Parameters
    ----------
    d : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.

    """
    result = {}
    for key, value in d.items():
        if isinstance(value, dict):
            inner_result = merge_relations(value)
            if 'parent-child relation' in inner_result:
                relation_type = inner_result['parent-child relation']
                del inner_result['parent-child relation']
                if relation_type not in result:
                    result[relation_type] = []
                result[relation_type].append(inner_result)
            else:
                result[key] = inner_result
        else:
            result[key] = value
    return result

#%% Load excel datasheets
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

#%% Get ontology entity for every parameter code
object_code_ontology_map = {}
for _, row in schema_metadata.iterrows():
    parameter_code = row["openBIS"]
    if is_nan(parameter_code) == False and is_nan(row["Ontology"]) == False and is_nan(row["Unit"]):
        object_code_ontology_map[parameter_code] = row["Ontology"]

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
                objects_metadata[col_name] = objects_metadata[col_name].str.replace(" ", "T")
        
        # Save the objects according to the type
        all_objects_metadata[sheet_name] = objects_metadata

# Close the Excel object
experiment_objects_excel.close()

# Generate matrix containing all the parent-child relations for all objects
all_unique_objects_ids = pd.unique(experiment_metadata[['Object 1', 'Object 2']].values.ravel('K'))
all_objects_relations = pd.DataFrame(0, index = all_unique_objects_ids, columns = all_unique_objects_ids)
for idx, object_1_id in enumerate(experiment_metadata["Object 1"]):
    relation_id = experiment_metadata["Relation"][idx]
    object_2_id = experiment_metadata["Object 2"][idx]
    all_objects_relations.loc[object_1_id, object_2_id] = relation_id

#%% Generate dictionary that is going to be used to generate the JSON-LD file
selected_object = "PUBL1"
all_objects_relations_dict = compute_jsonld_data(all_objects_relations, object_code_ontology_map, schema_ontology, all_objects_metadata, selected_object)
all_objects_relations_dict_merged = merge_relations(all_objects_relations_dict)
all_objects_relations_dict_merged["@graph"] = all_objects_relations_dict_merged["@graph"]["PUBL1"]

#%% Export to JSON-LD
jsonld_object = json.dumps(all_objects_relations_dict_merged, indent=4)
 
# Writing to sample.json
with open("selected_object_schema.json", "w") as outfile:
    outfile.write(jsonld_object)

"""
Tasks:
    3 - Link the parameters to the units (meters, Volts, Amperes, etc.)
    4 - Link the description given in the Excel file
    5 - Replace openBIS ID by hasPart or other relation in JSON-LD file
"""


