# from django.shortcuts import render
# THis file is saving provenance information about each sgp the main functionality
# is done in iknow_manager.

# hello from tarek, will add prov data capture to existing functions

import pandas as pd
from django.core.exceptions import ObjectDoesNotExist

from planthub.iknow_datasets.models import Dataset
from planthub.iknow_datasets.views import dataset_from_key

from .models import SGP
from planthub.iknow_sgpc.models import SGPC

import os
import prov
from prov.model import ProvDocument, Namespace, Literal, PROV, Identifier, PROV_TYPE
from prov.dot import prov_to_dot
 
import json
import ast 


#def sgp_create() -> SGP:
#    """
#    Creates a new sgp.
#    """
#    new_sgp = SGP()
#    new_sgp.save()

#    return new_sgp

def sgp_create() -> SGP:
    """
    Creates a new sgp.
    """
    new_sgp = SGP()
    new_sgp.save()

    return new_sgp


def sgp_from_key(key: str) -> SGP:
    """
    Returns a safely obtained instance of SGP
    from a given key.
    """
    if key is None:
        return False

    # get SGP istance
    try:
        sgp: SGP = SGP.objects.get(id=key)
    except ObjectDoesNotExist:
        # sgp_pk was no valid primary key
        print("sgp not valid error")
        return False

    return sgp


def sgp_set_phase_state(sgp: SGP, new_state: str):
    """
    Set the state of the current phase in the provenance
    record of the given sgp.
    """
    cur_phase_num = str(len(sgp.provenanceRecord)-1)
    sgp.provenanceRecord[cur_phase_num]["state"] = new_state

    sgp.save()


def sgp_append_linking_step(sgp: SGP, input_pk, output_pk, method: str = "iknow-method"):
    """
    On start of linking tool, appends information
    in the provenance record.
    """
    next_step = str(len(sgp.provenanceRecord))
    sgp.provenanceRecord[next_step] = {}
    sgp.provenanceRecord[next_step]["type"] = "linking"
    sgp.provenanceRecord[next_step]["actions"] = {}
    sgp.provenanceRecord[next_step]["actions"]["input"] = input_pk
    sgp.provenanceRecord[next_step]["actions"]["output"] = output_pk
    sgp.provenanceRecord[next_step]["actions"]["method"] = method
    sgp.provenanceRecord[next_step]["state"] = "running"

    sgp_generate_provenance(sgp)
    
    sgp.save()


def append_cleaning_step(sgp: SGP, method, d_pk_in, d_pk_out):
    """
    On start of cleaning tool, appends information
    in the provenance record.
    """
    next_step = str(len(sgp.provenanceRecord))
    sgp.provenanceRecord[next_step] = {}
    sgp.provenanceRecord[next_step]["type"] = "cleaning"
    sgp.provenanceRecord[next_step]["actions"] = {}
    sgp.provenanceRecord[next_step]["actions"]["input"] = d_pk_in
    sgp.provenanceRecord[next_step]["actions"]["output"] = d_pk_out
    sgp.provenanceRecord[next_step]["actions"]["method"] = method

    sgp_generate_provenance(sgp)

    sgp.save()


def sgp_append_mapping_step(sgp: SGP, edits: dict, method: str = "iknow-method"):
    """
    Appends information of user edits on the linkingresult,
    to the provenance record.
    """
    next_step = str(len(sgp.provenanceRecord))
    print(next_step)
    print("hello form next step ")
    sgp.provenanceRecord[next_step] = {}
    sgp.provenanceRecord[next_step]["type"] = "editmapping"
    sgp.provenanceRecord[next_step]["edits"] = edits
    sgp.provenanceRecord[next_step]["actions"] = {}
    sgp.provenanceRecord[next_step]["actions"]["method"] = method

    sgp_generate_provenance(sgp)

    sgp.save()


def sgp_append_cpa_step(sgp: SGP, method: str = "iknow-method"):
    """
    Appends empty phase, marking cpamapping as completed.
    """
    next_step = str(len(sgp.provenanceRecord))
    sgp.provenanceRecord[next_step] = {}
    sgp.provenanceRecord[next_step]["type"] = "editcpa"
    sgp.provenanceRecord[next_step]["actions"] = {}
    sgp.provenanceRecord[next_step]["actions"]["method"] = method

    sgp_generate_provenance(sgp)

    sgp.save()


def sgp_append_schema_step(sgp: SGP, method: str = "iknow-method"):
    """
    Appends empty phase, marking schemarefinement as completed.
    """
    next_step = str(len(sgp.provenanceRecord))
    sgp.provenanceRecord[next_step] = {}
    sgp.provenanceRecord[next_step]["type"] = "schemarefine"
    sgp.provenanceRecord[next_step]["actions"] = {}
    sgp.provenanceRecord[next_step]["actions"]["method"] = method

    sgp_generate_provenance(sgp)

    sgp.save()


def sgp_append_init_step(sgp: SGP, init_data, method: str = "iknow-method"):
    sgp.provenanceRecord[0] = {}
    sgp.provenanceRecord[0]["type"] = "init"
    sgp.provenanceRecord[0]["selection"] = init_data
    sgp.provenanceRecord[0]["actions"] = {}
    sgp.provenanceRecord[0]["actions"]["method"] = method

    sgp_generate_provenance(sgp)

    sgp.save()


def sgp_append_querybuilding_step(sgp: SGP, method: str = "iknow-method"):
    """
    Appends empty phase, marking schemarefinement as completed.
    """
    next_step = str(len(sgp.provenanceRecord))
    sgp.provenanceRecord[next_step] = {}
    sgp.provenanceRecord[next_step]["type"] = "querybuilding"
    sgp.provenanceRecord[next_step]["actions"] = {}
    sgp.provenanceRecord[next_step]["actions"]["method"] = method

    sgp_generate_provenance(sgp)

    sgp.save()


def sgp_append_downloading_step(sgp: SGP, method: str = "iknow-method"):
    """
    Appends empty phase, marking schemarefinement as completed.
    """
    next_step = str(len(sgp.provenanceRecord))
    sgp.provenanceRecord[next_step] = {}
    sgp.provenanceRecord[next_step]["type"] = "downloading"
    sgp.provenanceRecord[next_step]["actions"] = {}
    sgp.provenanceRecord[next_step]["actions"]["method"] = method

    sgp_generate_provenance(sgp)
    
    sgp.save()

def sgp_generate_provenance(sgp: SGP):
    print('provfunctest')
    d1 = ProvDocument()
    d1.add_namespace('prov', 'http://www.w3.org/ns/prov#')
    d1.add_namespace('iknow', 'https://planthub.idiv.de/iknow/wiki/')

    e_iknow_sgpc = d1.entity(
        'iknow:sgpc', (
        ('prov:type', PROV['Collection']),
        ('prov:name', sgp.associated_bioproject)
        )
    )
    e_iknow_sgp = d1.entity(
        'iknow:sgp', (
        ('prov:type', PROV['Plan']),
        ('iknow:bioproject', sgp.associated_bioproject)
        )
    )
    d1.hadMember(e_iknow_sgpc, e_iknow_sgp)
    #e_iknow_sgp.add_asserterd_type('prov:Collection')
    
    # testing prov
    # TODO? json load before loop
    for key, phase in sgp.provenanceRecord.items():
        print(phase)
#--------------------------------------------------------------------------
#get all data from 'init' phase 
        if phase['type'] == 'init':
            a_phase_init = d1.activity(
                'prov:phase_init', other_attributes=(
                    ('prov:type', PROV['Collection']),
                    (PROV_TYPE, 'process'),
                    ('prov:name', str(phase['type'])),
                    ('iknow:method', str(phase['actions']['method'])),
                )
            )
            e_source_dataset = d1.entity(
                'iknow:source_dataset', (
                ('iknow:source', str(sgp.original_filename)),
                )
            )
            d1.used(a_phase_init, e_source_dataset)
            d1.wasAssociatedWith(a_phase_init, e_iknow_sgp)
            #a_init_action = d1.activity('prov:init_action', None, None, {PROV_TYPE: 'iknow:method', 'prov:value': str(phase['actions']['method'])})
            #d1.wasGeneratedBy(e_phase_init, a_phase_init, None, {'ex:fct': "save"})
           
            # read data from selection (datapoints, coloumn data type)
    #----------------------------------------------------------------------
    #get all data from 'selection' subfield; turn the data into entities
            for values in phase['selection']:
                ##print('values: ', values)
                for keys in phase['selection'].values():
                    ##print('data: ', keys)
                    for val in keys:
                ###DONT DELETE YET        
                        ##print('key, value: ',val,' ', keys[str(val)])
                        #create prov entity in range of 'val'; append all properties using 'val' as keys 
#-----------------------entity for each datapoint                        
                        #tempname = 'e_datapoint_' + str(val)
                        #tempname = d1.entity(
                        #    'prov:datapoint_' + str(val), (
                        #    (PROV_TYPE, 'datapoint'),
                        #    ('prov:name', 'datapoint_'+str(val)),
                        #   ('iknow:'+str(values), keys[str(val)]),
                        #    )
                        #)

#-----------------------entity for each 'coloumn' aka for type, child, parent, mapping, subject
                        e_typedata = d1.entity(
                                'iknow:type', (
                                    ('iknow:type', str(phase['selection']['type'])),
                                )
                            )
                        
                        e_childdata = d1.entity(
                                'iknow:child', (
                                    ('iknow:child', str(phase['selection']['child'])),
                                )
                            )
                        
                        e_parentdata = d1.entity(
                                'iknow:parent', (
                                    ('iknow:parent', str(phase['selection']['parent'])),
                                )
                            )
                        
                        e_mappingdata = d1.entity(
                                'iknow:mapping', (
                                    ('iknow:mapping', str(phase['selection']['mapping'])),
                                )
                            )
                        
                        e_subjectdata = d1.entity(
                                'iknow:subject', (
                                    ('iknow:subject', str(phase['selection']['subject'])),
                                )
                            )
            e_selection = d1.entity(
                'iknow:selection', (
                ('prov:type', PROV['Collection']),
                )
            )
            d1.hadMember(e_selection, e_typedata)
            d1.hadMember(e_selection, e_childdata)
            d1.hadMember(e_selection, e_parentdata)
            d1.hadMember(e_selection, e_mappingdata)
            d1.hadMember(e_selection, e_subjectdata)

            d1.wasGeneratedBy(e_selection, a_phase_init)
            d1.wasDerivedFrom(e_selection, e_source_dataset)                
#----------------------------------------------------------------------                   
        # for linking we need type, state, actions{input, method, output}                       
        if phase['type'] == 'linking':
            print('testlinking')
            print(str(phase['actions']['input']))
            print(str(phase['actions']['method']))
            print(str(phase['actions']['output']))

            a_phase_linking = d1.activity(
                'prov:phase_linking', other_attributes=(
                    (PROV_TYPE, "process"),
                    ('prov:name', str(phase['type'])),
                    ('iknow:state', str(phase['state'])),
                    ('iknow:actions_input', str(phase['actions']['input'])),
                    ('iknow:actions_method', str(phase['actions']['method'])),
                    ('iknow:actions_output', str(phase['actions']['output'])),
                )
            )
            d1.wasAssociatedWith(a_phase_linking, e_iknow_sgp)
            d1.used(a_phase_linking, e_selection)
            e_linking_output = d1.entity(
                'iknow:linking_output', (
                ('prov:id', str(phase['actions']['output'])),
                )
            )
            d1.wasGeneratedBy(e_linking_output, a_phase_linking)
            d1.wasDerivedFrom(e_linking_output, e_selection)
#----------------------------------------------------------------------
        # editcpa
        if phase['type'] == 'editcpa':
            print('testeditcpa')
            a_phase_editcpa = d1.activity(
                'prov:phase_edit_cpa', other_attributes=(
                    (PROV_TYPE, "process"),
                    ('prov:name', str(phase['type'])),
                    ('iknow:method', str(phase['actions']['method'])),
                )
            )
            d1.wasAssociatedWith(a_phase_editcpa, e_iknow_sgp)
            d1.used(a_phase_editcpa, e_linking_output)
            e_editcpa_output = d1.entity(
                'iknow:editcpa_output', (
                ('prov:id', 'PLACEHOLDER'),
                )
            )
            d1.wasGeneratedBy(e_editcpa_output, a_phase_editcpa)
            d1.wasDerivedFrom(e_editcpa_output, e_linking_output)
#----------------------------------------------------------------------
        # schemarefine
        if phase['type'] == 'schemarefine':
            print('testschemarefine')
            a_phase_schemarefine = d1.activity(
                'prov:phase_schema_refine', other_attributes= (
                    (PROV_TYPE, "process"),
                    ('prov:name', str(phase['type'])),
                    ('iknow:method', str(phase['actions']['method'])),
                )
            )
            d1.wasAssociatedWith(a_phase_schemarefine, e_iknow_sgp)
            d1.used(a_phase_schemarefine, e_editcpa_output)
            e_schemarefine_output = d1.entity(
                'iknow:schemarefine_output', (
                ('prov:id', 'PLACEHOLDER'),
                )
            )
            d1.wasGeneratedBy(e_schemarefine_output, a_phase_schemarefine)
            d1.wasDerivedFrom(e_schemarefine_output, e_editcpa_output)
#----------------------------------------------------------------------
        if phase['type'] == 'downloading':
            a_phase_downloading = d1.activity(
                'prov:phase_downloading', other_attributes=(
                    (PROV_TYPE, "process"),
                    ('prov:name', str(phase['type'])),
                    ('iknow:method', str(phase['actions']['method'])),
                )
            )
            d1.wasAssociatedWith(a_phase_downloading, e_iknow_sgp)
            d1.used(a_phase_downloading, e_schemarefine_output)
            e_downloading_output = d1.entity(
                'iknow:downloading_output', (
                ('prov:status', 'completed'),
                )
            )
            d1.wasGeneratedBy(e_downloading_output, a_phase_downloading)
            d1.wasDerivedFrom(e_downloading_output, e_schemarefine_output)
#----------------------------------------------------------------------    
    #print(d1.get_provn())
    d1.serialize('article-prov5.ttl', format='rdf', rdf_format='ttl')
    #print(d1.serialize())
#----------------------------------------------------------------------
    #visualization
    #add visualization to PATH
    os.environ["PATH"] += os.pathsep + 'C:/Program Files (x86)/Graphviz2.38/bin/'

    dot = prov_to_dot(d1, direction='RL')
    dot.write_png('provIMG.png')

    #print(sgp.source_dataset)
    print('--------------')
    print(str(sgp.source_dataset.all()[0]))
    
    print(str())

    sgp.save()


def sgp_get_output_file(sgp: SGP) -> Dataset:
    """
    Returns latest output dataset or source dataset
    (if in init phase). Returns False if error.
    """

    cur_phase_num = len(sgp.provenanceRecord)-1

    # if in init phase
    if cur_phase_num <= 1:
        if sgp.source_dataset.all().count() > 0:
            return sgp.source_dataset.all()[0]
        else:
            # No source dataset found in sgp
            return False

    for i in range(cur_phase_num, -1, -1):
        try:
            phase_type = sgp.provenanceRecord[str(i)]["type"]
        except KeyError:
            # No phase type found in sgp:
            return False

        if phase_type == "linking" or phase_type == "cleaning":
            try:
                # get latest output dataset
                dataset_pk = sgp.provenanceRecord[str(i)]["actions"]["output"]
                dataset = dataset_from_key(dataset_pk)

                return dataset
            except KeyError:
                # No action or output key found in sgp
                return False
        elif phase_type == "init":
            if sgp.source_dataset.all().count() > 0:
                return sgp.source_dataset.all()[0]
            else:
                # No source dataset found in sgp
                return False

    return False


def sgp_get_mapping_file(sgp: SGP) -> Dataset:
    """
    Returns the mapping file (linking result output),
    or False if an error occured.
    """
    cur_phase_num = len(sgp.provenanceRecord)-1

    for i in range(cur_phase_num, -1, -1):
        try:
            phase_type = sgp.provenanceRecord[str(i)]["type"]
        except KeyError:
            # No phase type found in sgp
            return False

        if phase_type == "linking":
            try:
                # get linking output dataset
                dataset_pk = sgp.provenanceRecord[str(i)]["actions"]["output"]
                dataset = dataset_from_key(dataset_pk)

                return dataset
            except KeyError:
                # No action or output key found in sgp
                return False

    return False


def sgp_get_input_file(sgp: SGP) -> Dataset:
    """
    Returns latest input dataset or source dataset
    (if in init phase). Returns False if error.
    """

    cur_phase_num = len(sgp.provenanceRecord)-1

    # if in init phase
    if cur_phase_num <= 1:
        if sgp.source_dataset.all().count() > 0:
            return sgp.source_dataset.all()[0]
        else:
            # No source dataset found in sgp
            return False

    for i in range(cur_phase_num, -1, -1):
        try:
            phase_type = sgp.provenanceRecord[str(i)]["type"]
        except KeyError:
            # No phase type found in sgp:
            return False

        if phase_type == "linking" or phase_type == "cleaning":
            try:
                # get latest output dataset
                dataset_pk = sgp.provenanceRecord[str(i)]["actions"]["input"]
                dataset = dataset_from_key(dataset_pk)

                return dataset
            except KeyError:
                # No action or output key found in sgp
                return False
        elif phase_type == "init":
            if sgp.source_dataset.all().count() > 0:
                return sgp.source_dataset.all()[0]
            else:
                # No source dataset found in sgp
                return False

    return False


def sgp_get_col_types(sgp: SGP, binary=False):
    """
    Returns string-list of types (String, Integer, ...)
    for each column. String = 1 and other = 0 if binary
    is True.
    """
    selections = sgp.provenanceRecord['0']['selection']
    col_types = []

    for x in range(len(selections['type'].keys())):
        try:
            if binary:
                selected_type = selections['type'][str(x)]
                if selected_type == 'String':
                    col_types.append(1)
                else:
                    col_types.append(0)
            else:
                col_types.append(selections['type'][str(x)])
        except Exception:
            # Key not were its supposed to be in prov rec
            return False

    return col_types


def get_last_phasetype(sgp: SGP):
    """
    Return the current type of the latest
    entry in the provenance record of the
    given sgp. ['init', 'cleaning', 'linking']
    """
    index = len(sgp.provenanceRecord)-1
    if index < 0:
        return False
    elif index > 0:
        sgp.provenanceRecord[str(index)]["type"]
    else:
        return False


def sgp_in_progress(sgp: SGP):
    """
    Checks if tool is running for a given sgp.
    """
    cur_phase_num = str(len(sgp.provenanceRecord)-1)

    if cur_phase_num not in sgp.provenanceRecord:
        return False

    if "state" not in sgp.provenanceRecord[cur_phase_num]:
        return False

    cur_state = sgp.provenanceRecord[cur_phase_num]["state"]
    if cur_state == "running":
        return True
    else:
        return False


def get_header_mapping(sgp: SGP):
    return list(sgp.provenanceRecord['0']['selection']['mapping'].values())


def get_original_header(sgp: SGP):
    return list(sgp.original_table_header.values())


def sgp_get_provrec(sgp_pk):
    """
    Returns provenance record for given sgp_pk, or
    False if sgp does not exist.
    """
    sgp = sgp_from_key(sgp_pk)

    if sgp is False:
        return False

    return sgp.provenanceRecord


def sgp_replace_mapping_file_with_copy(sgp: SGP):
    """
    Copies and replaces the mapping file in a SGP.
    If there is no linking phase, or the Dataset object does
    not exist --> currently does nothing.
    """
    for key, phase in sgp.provenanceRecord.items():
        if phase['type'] == 'linking':
            output_pk = phase['actions']['output']
            try:
                old_dataset = Dataset.objects.get(pk=output_pk)
            except ObjectDoesNotExist:
                break

            old_dataset.pk = None
            old_dataset.save()
            phase['actions']['output'] = old_dataset.pk

            sgp.save()


def sgp_edit_mapping(sgp: SGP, edits: dict):
    """
    Applies user edits on the linking result,
    to the specific cells in the mapping file.
    """
    if len(edits) == 0:
        return

    mapping_dataset = sgp_get_mapping_file(sgp)
    df = pd.read_csv(mapping_dataset.file_field.path)

    # TODO: apply edit on all occurences here
    for key in edits:
        try:
            col = int(edits[key]['col'])
            row = int(edits[key]['row'])
            df.iat[row, col] = str(edits[key]['value'])
        except KeyError:
            # TODO: - handle error
            # incorrect edits
            break

    df.to_csv(mapping_dataset.file_field.path, index=False)


def sgp_replace_source_dataset(sgp: SGP, new_dataset: Dataset):
    """
    Replaces source dataset of the sgp.
    """
    sgp.source_dataset.clear()
    sgp.source_dataset.add(new_dataset)
    sgp.datasets_copied = False
    sgp.save()


def sgp_undo_till_linking(sgp: SGP):
    """
    Undoes every phase in an sgp, until (not including) the
    linking phase. Does not delete datasets/files.
    """
    prov_rec = sgp.provenanceRecord
    for i in range(len(sgp.provenanceRecord)-1, 0, -1):
        cur_type = prov_rec[str(i)]['type']

        if cur_type == "editcpa":
            del prov_rec[str(i)]
        elif cur_type == "editmapping":
            del prov_rec[str(i)]
        elif cur_type == "schemarefine":
            del prov_rec[str(i)]

    sgp.save()
