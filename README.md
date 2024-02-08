# nanotech-premise

* Excel file contains seven datasheets:
    - The "Metadata Schema" contains the objects necessary to map the experiments and the simulations. It comprises ten columns:
        - "Metadata": The name of the object/property (metadata);
        - "Unit": The unit used on the respective metadata;
        - "Input": Who introduces the value oof the respective metadata;
        - "Description": A small description of the respective metadata;
        - "Ontology": The name of the respective metadata in the used semantic schema;
        - "openBIS" The name of respetive metadata in the openBIS software;
        - "openBIS datatye": The datatype of the respetive metadata inside openBIS;
        - "Comments": Some comments to the respetive metadata;
        - "is Parameter already created?": To verify whether the respective metadata is already present in the "openBIS - parameters" datasheet;
        - "is Entity already created?": To verify whether the respective metadata is already present in the "Ontology - definition" datasheet.
    - The "Metadata Updates" contains some tasks that should be performed to improve the "Metadata Schema";
    - The "Ontology - definition" contains the IRI links to the different ontologies. It comprises three columns:
        - "Entity": The name given to the respective metadata;
        - "IRI": The link to the ontology that defines the respective metadata;
        - "Type": The datatype of the respective metadata.
    - The "openBIS - parameters" contains the definitions necessary to create the property types inside openBIS. It comprises seven columns:
        - "Code": Code of the property type inside openBIS;
        - "Label": Label of the property type inside openBIS;
        - "Description": Description of the property type inside openBIS;
        - "DataType": Datatype of the property type inside openBIS;
        - "managedInternally": Whether the property type is managed internally in openBIS;
        - "Vocabulary": Vocabulary of the property type inside openBIS, in the case, the property is a CONTROLLEDVOCABULARY datatype;
        - "Metadata": Type of widget used in the case of property types that are MULTILINE_VARCHAR or XML.
    - The "openBIS - vocabulary" contains the vocabularies used in openBIS. It comprises two columns:
        - "Vocabulary": The code of the vocabulary inside openBIS;
        - "Description": Description of the respective vocabulary inside openBIS.
    - The "openBIS - vocabulary terms" contains the terms used in vocabularies in openBIS. It comprises four columns:
        - "Vocabulary": The code of the vocabulary inside openBIS;
        - "Term code": The code of the term inside openBIS;
        - "Term label": The label of the term inside openBIS;
        - "Term description": The description of the term inside openBIS;
    - The "Legend" contains a column with colors and a column with the legend of the colors. These colors are used in the "Metadata Schema" while developing it.

* "from_datasheet_to_openbis.py" is used to create the objects, property types, and vocabulary types in the openBIS considering the information gathered in the Excel file. After creating the metadata objects, one can populate the openBIS and create relations between different objects.
* "export_from_openbis_to_jsonld.py" is used to export an object (selected by the user) from openBIS to JSON-LD.
* "selected_object_schema.jsonld" is an example of an JSON-LD file obtained from exporting a Publication from the openBIS. This JSON-LD can be explored in the [JSON-LD Playground](https://json-ld.org/playground/). One just needs to copy its content into the textbox displayed in the playground and click on the "Visualized" tab below it.

## Acknowledgements
We acknowledge support from:
* the [NCCR MARVEL](http://nccr-marvel.ch/) funded by the Swiss National Science Foundation;
* the [PREMISE](https://ord-premise.github.io/) project supported by the [Open Research Data Program](https://ethrat.ch/en/eth-domain/open-research-data/) of the ETH Board.

<img src="https://raw.githubusercontent.com/aiidateam/aiida-quantumespresso/develop/docs/source/images/MARVEL.png" width="250px" height="131px"/>
<img src="https://github.com/ord-premise/ord-premise.github.io/blob/main/assets/img/logos/PREMISE-logo.svg" width="300px" height="131px"/>
<img src="https://ethrat.ch/wp-content/uploads/2021/12/ethr_en_rgb_black.svg" width="300px" height="131px"/>

