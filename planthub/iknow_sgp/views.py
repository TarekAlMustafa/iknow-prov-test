# from django.shortcuts import render

from django.core.exceptions import ObjectDoesNotExist

from planthub.iknow_datasets.models import Dataset

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


def append_linking_step(sgp: SGP, method, input_pk, output_pk):
    """
    On start of linking tool, appends information
    in the provenance record.
    """
    cur_step = len(sgp.provenanceRecord)
    sgp.provenanceRecord[cur_step] = {}
    sgp.provenanceRecord[cur_step]["type"] = "linking"
    sgp.provenanceRecord[cur_step]["actions"] = {}
    sgp.provenanceRecord[cur_step]["actions"]["input"] = input_pk
    sgp.provenanceRecord[cur_step]["actions"]["output"] = output_pk
    sgp.provenanceRecord[cur_step]["actions"]["method"] = method
    sgp.provenanceRecord[cur_step]["state"] = "running"

    sgp.save()


def append_cleaning_step(self, sgp: SGP, method, d_pk_in, d_pk_out):
    cur_step = len(sgp.provenanceRecord)
    sgp.provenanceRecord[cur_step] = {}
    sgp.provenanceRecord[cur_step]["type"] = "cleaning"
    sgp.provenanceRecord[cur_step]["actions"] = {}
    sgp.provenanceRecord[cur_step]["actions"]["input"] = d_pk_in
    sgp.provenanceRecord[cur_step]["actions"]["output"] = d_pk_out
    sgp.provenanceRecord[cur_step]["actions"]["method"] = method

    sgp.save()


def get_latest_dataset(sgp: SGP) -> Dataset:
    """
    Return the latest dataset for the given sgp.
    [Not completely implemented]
    """
    # <= 1 ... INIT PHASE
    if len(sgp.provenanceRecord) <= 1:
        # print("The source dataset for sgp: ", sgp.pk, " is ", sgp.source_dataset.all()[0])
        return sgp.source_dataset.all()[0]
    else:
        last_phasetype = get_last_phasetype(sgp)

        # CLEANING PHASE
        if last_phasetype == "cleaning":
            return sgp.source_dataset.all()[0]
        # LINKING PHASE
        elif last_phasetype == "linking":
            return sgp.source_dataset.all()[0]
        # ELSE
        else:
            return sgp.source_dataset.all()[0]


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
    [Not completely implemented]
    """
    return False
