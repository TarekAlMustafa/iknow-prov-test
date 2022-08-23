# from django.shortcuts import render

from planthub.iknow_datasets.models import Dataset

from .models import SGP


def createSGP(bioprojectname: str):
    new_sgp = SGP()

    new_sgp.bioprojectname = bioprojectname

    new_sgp.save()

    return new_sgp


def start_linking_step(sgp: SGP, method, output_pk):
    pass


def append_linking_step(sgp: SGP, method, input_pk, output_pk):
    cur_step = len(sgp.provenanceRecord)
    sgp.provenanceRecord[cur_step] = {}
    sgp.provenanceRecord[cur_step]["type"] = "linking"
    sgp.provenanceRecord[cur_step]["actions"] = {}
    sgp.provenanceRecord[cur_step]["actions"]["input"] = input_pk
    sgp.provenanceRecord[cur_step]["actions"]["output"] = output_pk
    sgp.provenanceRecord[cur_step]["actions"]["method"] = method
    sgp.provenanceRecord[cur_step]["state"] = "running"

    sgp.save()


# depending on the last phase type in each sgp, this
# function returns the latest dataset object in the sgp
def get_latest_dataset(sgp: SGP) -> Dataset:
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
    index = len(sgp.provenanceRecord)-1
    if index == 0:
        return "empty"
    elif index > 0:
        sgp.provenanceRecord[str(index)]["type"]
    else:
        return False


def is_in_progress(sgp: SGP):
    return False
