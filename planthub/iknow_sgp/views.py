# from django.shortcuts import render

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


def append_linking_step(sgp: SGP, method, input_pk, output_pk):
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


def append_editMapping_step(sgp: SGP):
    next_step = str(len(sgp.provenanceRecord))
    sgp.provenanceRecord[next_step] = {}
    sgp.provenanceRecord[next_step]["type"] = "editmapping"

    sgp.save()


def append_editCpa_step(sgp: SGP):
    next_step = str(len(sgp.provenanceRecord))
    sgp.provenanceRecord[next_step] = {}
    sgp.provenanceRecord[next_step]["type"] = "editcpa"

    sgp.save()


def append_schemaRefine_step(sgp: SGP):
    next_step = str(len(sgp.provenanceRecord))
    sgp.provenanceRecord[next_step] = {}
    sgp.provenanceRecord[next_step]["type"] = "schemarefine"

    sgp.save()


def get_latest_dataset(sgp: SGP) -> Dataset:
    """
    Return the latest dataset for the given sgp.
    """

    cur_step_num = len(sgp.provenanceRecord)-1

    # <= 1 ... INIT PHASE
    if cur_step_num <= 0:
        # print("The source dataset for sgp: ", sgp.pk, " is ", sgp.source_dataset.all()[0])
        return sgp.source_dataset.all()[0]
    else:
        if str(cur_step_num) in sgp.provenanceRecord:
            if "actions" in sgp.provenanceRecord[str(cur_step_num)]:
                if "output" in sgp.provenanceRecord[str(cur_step_num)]["actions"]:
                    dataset_pk = sgp.provenanceRecord[str(cur_step_num)]["actions"]["output"]

                    dataset = dataset_from_key(dataset_pk)

                    return dataset

        # else... some error happend or something went wrong along the way
        return False


def get_latest_input_dataset(sgp: SGP) -> Dataset:

    cur_step_num = len(sgp.provenanceRecord)-1

    # <= 1 ... INIT PHASE
    if cur_step_num <= 0:
        # print("The source dataset for sgp: ", sgp.pk, " is ", sgp.source_dataset.all()[0])
        return sgp.source_dataset.all()[0]
    else:
        if str(cur_step_num) in sgp.provenanceRecord:
            if "actions" in sgp.provenanceRecord[str(cur_step_num)]:
                if "input" in sgp.provenanceRecord[str(cur_step_num)]["actions"]:
                    dataset_pk = sgp.provenanceRecord[str(cur_step_num)]["actions"]["input"]

                    dataset = dataset_from_key(dataset_pk)

                    return dataset

        # else... some error happend or something went wrong along the way
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
    given sgp. ['empty', 'init', 'cleaning', 'linking']
    """
    index = len(sgp.provenanceRecord)-1
    if index == 0:
        return "empty"
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


# this function was rushed and probably has bugs and errors. For the simple case
# its working now. But change it later.
def get_mapping_file(sgp: SGP):
    cur_step_int = len(sgp.provenanceRecord)-1

    if str(cur_step_int) not in sgp.provenanceRecord:
        return False

    if sgp.provenanceRecord[str(cur_step_int)]['type'] == 'linking':
        return get_latest_dataset(sgp)

    for i in range(cur_step_int, 0, -1):
        if sgp.provenanceRecord[str(i)]['type'] == 'linking':
            dataset_pk = sgp.provenanceRecord[str(i)]["actions"]["output"]

            dataset = dataset_from_key(dataset_pk)

            return dataset


def get_header_mapping(sgp: SGP):
    return list(sgp.provenanceRecord['0']['selection']['mapping'].values())


def get_original_header(sgp: SGP):
    return list(sgp.original_table_header.values())


def get_provrec(sgp_pk):
    sgp = sgp_from_key(sgp_pk)

    if sgp is False:
        return False

    return sgp.provenanceRecord
