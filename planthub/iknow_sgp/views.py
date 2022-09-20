# from django.shortcuts import render

import pandas as pd
from django.core.exceptions import ObjectDoesNotExist

from planthub.iknow_datasets.models import Dataset
from planthub.iknow_datasets.views import dataset_from_key

from .models import SGP


def create_sgp(bioprojectname: str):
    """
    Creates a new sgp with given Bioprojectname.
    """
    new_sgp = SGP()
    new_sgp.bioprojectname = bioprojectname
    new_sgp.save()

    return new_sgp


def sgp_from_key(key: str):
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


def set_phase_state(sgp: SGP, new_state: str):
    """
    Set the state of the current phase in the provenance
    record of the given sgp.
    """
    cur_step = str(len(sgp.provenanceRecord)-1)
    sgp.provenanceRecord[cur_step]["state"] = new_state
    sgp.save()


def append_linking_step(sgp: SGP, input_pk, output_pk, method: str = "iknow-method"):
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

    sgp.save()


def append_cleaning_step(sgp: SGP, method, d_pk_in, d_pk_out):
    next_step = str(len(sgp.provenanceRecord))
    sgp.provenanceRecord[next_step] = {}
    sgp.provenanceRecord[next_step]["type"] = "cleaning"
    sgp.provenanceRecord[next_step]["actions"] = {}
    sgp.provenanceRecord[next_step]["actions"]["input"] = d_pk_in
    sgp.provenanceRecord[next_step]["actions"]["output"] = d_pk_out
    sgp.provenanceRecord[next_step]["actions"]["method"] = method

    sgp.save()


def append_editMapping_step(sgp: SGP, edits: dict, method: str = "iknow-method"):
    next_step = str(len(sgp.provenanceRecord))
    sgp.provenanceRecord[next_step] = {}
    sgp.provenanceRecord[next_step]["type"] = "editmapping"
    sgp.provenanceRecord[next_step]["edits"] = edits
    sgp.provenanceRecord[next_step]["actions"] = {}
    sgp.provenanceRecord[next_step]["actions"]["method"] = method

    sgp.save()


def append_editCpa_step(sgp: SGP, method: str = "iknow-method"):
    next_step = str(len(sgp.provenanceRecord))
    sgp.provenanceRecord[next_step] = {}
    sgp.provenanceRecord[next_step]["type"] = "editcpa"
    sgp.provenanceRecord[next_step]["actions"] = {}
    sgp.provenanceRecord[next_step]["actions"]["method"] = method

    sgp.save()


def append_schemaRefine_step(sgp: SGP, method: str = "iknow-method"):
    next_step = str(len(sgp.provenanceRecord))
    sgp.provenanceRecord[next_step] = {}
    sgp.provenanceRecord[next_step]["type"] = "schemarefine"
    sgp.provenanceRecord[next_step]["actions"] = {}
    sgp.provenanceRecord[next_step]["actions"]["method"] = method

    sgp.save()


def get_latest_output_dataset(sgp: SGP) -> Dataset:
    """
    Searches backwards through provenance record and returns
    the latest output dataset. If the latest is in init-phase
    -> returns source dataset. Returns False if error.
    """

    cur_step_num = len(sgp.provenanceRecord)-1

    if cur_step_num <= 1:
        if sgp.source_dataset.all().count() > 0:
            return sgp.source_dataset.all()[0]
        else:
            print("No source dataset found in sgp: ", sgp.pk)
            return False

    for i in range(cur_step_num, -1, -1):
        try:
            phase_type = sgp.provenanceRecord[str(i)]["type"]
        except KeyError:
            print("No phase type found in sgp: ", sgp.pk, " phase: ", i)
            return False

        if phase_type == "linking" or phase_type == "cleaning":
            try:
                dataset_pk = sgp.provenanceRecord[str(i)]["actions"]["output"]
                print("Loading dataset with pk: ", dataset_pk)
                dataset = dataset_from_key(dataset_pk)
                print("Returning dataset: ", dataset)
                return dataset
            except KeyError:
                print("No action or output key found in sgp: ", sgp.pk, " phase: ", i)
                return False
        elif phase_type == "init":
            if sgp.source_dataset.all().count() > 0:
                return sgp.source_dataset.all()[0]
            else:
                print("No source dataset found in sgp: ", sgp.pk, " phase: ", i)
                return False

    return False


def get_mapping_dataset(sgp: SGP) -> Dataset:
    cur_step_num = len(sgp.provenanceRecord)-1

    for i in range(cur_step_num, -1, -1):
        try:
            phase_type = sgp.provenanceRecord[str(i)]["type"]
        except KeyError:
            print("No phase type found in sgp: ", sgp.pk, " phase: ", i)
            return False

        if phase_type == "linking":
            try:
                dataset_pk = sgp.provenanceRecord[str(i)]["actions"]["output"]
                print("Loading dataset with pk: ", dataset_pk)
                dataset = dataset_from_key(dataset_pk)
                print("Returning dataset: ", dataset)
                return dataset
            except KeyError:
                print("No action or output key found in sgp: ", sgp.pk, " phase: ", i)
                return False

    return False


def get_latest_input_dataset(sgp: SGP) -> Dataset:
    """
    Searches backwards through provenance record and returns
    the latest input dataset. If the latest is in init-phase
    -> returns source dataset. Returns False if error.
    """
    cur_step_num = len(sgp.provenanceRecord)-1

    if cur_step_num <= 1:
        if sgp.source_dataset.all().count() > 0:
            return sgp.source_dataset.all()[0]
        else:
            print("No source dataset found in sgp: ", sgp.pk)
            return False

    for i in range(cur_step_num, -1, -1):
        try:
            phase_type = sgp.provenanceRecord[str(i)]["type"]
        except KeyError:
            print("No phase type found in sgp: ", sgp.pk, " phase: ", i)
            return False

        if phase_type == "linking" or phase_type == "cleaning":
            try:
                dataset_pk = sgp.provenanceRecord[str(i)]["actions"]["input"]
                print("Loading dataset with pk: ", dataset_pk)
                dataset = dataset_from_key(dataset_pk)
                print("Returning dataset: ", dataset)
                return dataset
            except KeyError:
                print("No action or input key found in sgp: ", sgp.pk, " phase: ", i)
                return False
        elif phase_type == "init":
            if sgp.source_dataset.all().count() > 0:
                return sgp.source_dataset.all()[0]
            else:
                print("No source dataset found in sgp: ", sgp.pk, " phase: ", i)
                return False

    return False


def get_column_types(sgp: SGP, binary=False):
    selections = sgp.provenanceRecord['0']['selection']
    col_types = []

    for x in range(len(selections['type'].keys())):
        try:
            if binary:
                type = selections['type'][str(x)]
                if type == 'String':
                    col_types.append(1)
                else:
                    col_types.append(0)
            else:
                col_types.append(selections['type'][str(x)])
        except (Exception):
            print(f"Error: Key not were its supposed to be in prov rec {sgp.pk} ")
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


def is_in_progress(sgp: SGP):
    """
    Checks if tool is running for a given sgp.
    """
    cur_step = str(len(sgp.provenanceRecord)-1)

    if cur_step not in sgp.provenanceRecord:
        return False

    if "state" not in sgp.provenanceRecord[cur_step]:
        return False

    cur_state = sgp.provenanceRecord[cur_step]["state"]
    if cur_state == "running":
        return True
    else:
        return False


def get_header_mapping(sgp: SGP):
    return list(sgp.provenanceRecord['0']['selection']['mapping'].values())


def get_original_header(sgp: SGP):
    return list(sgp.original_table_header.values())


def get_provrec(sgp_pk):
    sgp = sgp_from_key(sgp_pk)

    if sgp is False:
        return False

    return sgp.provenanceRecord


def replace_mapping_file_with_copy(sgp: SGP):
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
            except (ObjectDoesNotExist):
                break

            old_dataset.pk = None
            old_dataset.save()
            phase['actions']['output'] = old_dataset.pk

            sgp.save()


def apply_mapping_edits_to_sgp(sgp: SGP, edits):
    # print("Applying edits: ")
    # print(edits)
    # print("to sgp ", sgp.pk)
    mapping_dataset = get_mapping_dataset(sgp)
    print("Found Mapping file: ", mapping_dataset.file_field.name)
    df = pd.read_csv(mapping_dataset.file_field.path)

    # TODO: apply edit on all occurences here
    for key in edits:
        col = int(edits[key]['col'])
        row = int(edits[key]['row'])
        print(f"col: {col} row: {row} original_val: {df.iat[row, col]}")
        df.iat[row, col] = str(edits[key]['value'])

    df.to_csv(mapping_dataset.file_field.path, index=False)


def replace_source_dataset(sgp: SGP, new_dataset: Dataset):
    sgp.source_dataset.clear()
    sgp.source_dataset.add(new_dataset)
    sgp.datasets_copied = False
    sgp.save()


def reset_sgp_until_linking(sgp: SGP):
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
