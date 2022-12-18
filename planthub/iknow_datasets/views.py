# from django.shortcuts import render
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from django.http import JsonResponse
import os
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File

from .models import Dataset

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
STORAGE_DIR = f"{settings.MEDIA_ROOT}/iknow_datasets_temp/"


def handle_uploaded_file(file, filename):
    """
    Saves uploaded file to database and returns
    the created dataset entry.
    """
    # TODO:
    #   - error handling

    # create the model instance
    datasetentry = Dataset()

    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    # pathlib seems to be the way to handle paths across all OS
    filepath = Path(f"{STORAGE_DIR}{unique_filename}")

    # write the file
    with open(filepath, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    # save file into database
    with open(filepath, 'rb') as doc_file:
        datasetentry.file_field.save(filename, File(doc_file), save=True)

    # save the instance
    datasetentry.save()

    # remove the temporary file
    os.remove(filepath)

    return datasetentry


def create_filefield(filename: str):
    """
    Creates dataset entry by creating new empty file. We create a new
    empty file to use it in in linkingresult.
    """
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    filepath = Path(f"{STORAGE_DIR}{unique_filename}")

    # write new empty temporary file
    with open(filepath, 'w') as my_new_csv_file:
        if my_new_csv_file:
            pass
        pass

    # create the model instance
    datasetentry = Dataset()

    # save file into database
    with open(filepath, 'rb') as doc_file:
        datasetentry.file_field.save(filename, File(doc_file), save=True)

    # save the instance
    datasetentry.save()

    # remove the temporary file
    os.remove(filepath)

    return datasetentry


def dataset_from_key(key: str):
    """
    Returns a safely obtained instance of Dataset
    from a given key.
    """
    if key is None:
        return False

    # get SGP instance
    try:
        dataset: Dataset = Dataset.objects.get(id=key)
    except ObjectDoesNotExist:
        # sgp_pk was no valid primary key
        print("dataset pk not valid error")
        return False

    return dataset
