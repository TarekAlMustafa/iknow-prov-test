# from django.contrib.auth import get_user_model
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.contrib.messages.views import SuccessMessageMixin
# from django.urls import reverse
# from django.utils.translation import gettext_lazy as _
# from django.views.generic import DetailView, RedirectView, UpdateView

import os
from django.db.models import Max
from django.db.models.functions import Lower
from django.http.response import HttpResponse, JsonResponse
from django.core import serializers
from .models import Dataset, Datastructure, DatastructureInline, File, get_file_path
from django.conf import settings
import pandas as pd
import numpy as np
from io import BytesIO as IO
import tarfile

# read xslx and create Http response object accordingly
def read_respond_xslx(filepath, name):
    PandasDataFrame = pd.read_excel(filepath)
    PandasDataFrame = PandasDataFrame.fillna("NA")

    # create IO stream to provide the requested file as a response
    sio = IO()
    PandasWriter = pd.ExcelWriter(sio, engine="xlsxwriter")
    PandasDataFrame.to_excel(PandasWriter, sheet_name="name", index=False)
    PandasWriter.save()
    sio.seek(0)
    # create response object
    response = HttpResponse(
        sio.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = "attachment; filename=" + name + ".xlsx"
    return response


# read csv and create Http response object accordingly
def read_respond_csv(filepath, name):
    PandasDataFrame = pd.read_csv(filepath)
    PandasDataFrame = PandasDataFrame.fillna("NA")

    # create response object
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=" + name + ".csv"
    PandasDataFrame.to_csv(path_or_buf=response, index=False)

    return response


# read gz and create Http response object accordingly
def read_respond_gz(filepath, name):
    tar_file = open(filepath, "rb")
    response = response = HttpResponse(tar_file, content_type="application/tar+gzip")
    response["Content-Disposition"] = "attachment; filename=" + name + ".gz"
    return response


# read other format and create Http response object accordingly
def other_format(filepath, name):
    pass


# method to download metadata
def download_metadata(request):
    name = request.GET["name"]
    version = request.GET.get("version", "latest")  # set latest as default version

    # retrieve latest version if no version or "latest" is mentioned in request query
    if version == "latest":
        version = (
            Datastructure.objects.annotate(name_lower=Lower("name"))
            .filter(name_lower=name)
            .aggregate(Max("version"))["version__max"]
        )

    # retrieve datastructure id from Datastructure's table to corresponding metadata
    datastructure_id = (
        Datastructure.objects.annotate(name_lower=Lower("name"))
        .filter(name_lower=name, version=version)
        .values()[0]["id"]
    )

    # retrieve metadata information and load into dataframe to ease data format conversion
    datastructureinline = DatastructureInline.objects.filter(
        datastructure_id=datastructure_id
    ).values("name", "short_name", "datatype")
    PandasDataFrame = pd.DataFrame(datastructureinline)

    # create response object
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=" + name + "_metadata.csv"
    PandasDataFrame.to_csv(path_or_buf=response, index=False)
    return response


# method to download data
def download_data(request):
    name = request.GET["name"]
    version = request.GET.get("version", "latest")  # set latest as default version
    format = request.GET.get("format", "csv")  # set csv a default format

    # retrieve dataset id to find respective media file path
    dataset = (
        Dataset.objects.annotate(title_lower=Lower("title"))
        .filter(title_lower=name)
        .values("id", "download")
    )
    dataset_id = dataset[0]["id"]
    dataset_download = dataset[0]["download"]
    if dataset_download:
        # retrieve latest version if no version or "latest" is mentioned in request query
        if version == "latest":
            version = File.objects.filter(dataset_id=dataset_id).aggregate(
                Max("version")
            )["version__max"]

        # get file path from the File database
        filename = File.objects.filter(dataset_id=dataset_id, version=version).values()[
            0
        ]["file"]

        data_filepath = os.path.join(settings.MEDIA_ROOT, filename)

        # get basename and extension of the file to read accordingly
        path, extension = os.path.splitext(data_filepath)
        basename = os.path.basename(path)

        # dict maps -> file extension with respective handler
        read_file_dict = {
            ".csv": read_respond_csv,
            ".xlsx": read_respond_xslx,
            ".gz": read_respond_gz,
        }

        response = read_file_dict.get(extension, other_format)(data_filepath, basename)

    return response
