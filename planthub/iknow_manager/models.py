# from django.db import models
from django.db import models


class CPAmapping(models.Model):
    s = models.CharField(max_length=4096)
    sLabel = models.CharField(max_length=4096)
    p = models.CharField(max_length=4096)
    pLabel = models.CharField(max_length=4096)
    o = models.CharField(max_length=4096)
    oLabel = models.CharField(max_length=4096)


class IKNOWproperty(models.Model):
    uri = models.CharField(unique=True, max_length=4096)
    label = models.CharField(max_length=4096)


class IKNOWclass(models.Model):
    uri = models.CharField(unique=True, max_length=4096)
    label = models.CharField(max_length=4096)


class QueryMetaData(models.Model):
    project_name = models.CharField(max_length=4096)
    column_name = models.CharField(max_length=4096)
    column_type = models.CharField(max_length=4096)
    column_category = models.CharField(max_length=4096)
    column_subcategory = models.CharField(max_length=4096)
    column_URI = models.CharField(max_length=4096)
    value = models.CharField(max_length=4096)
    ui_element_type = models.CharField(max_length=4096)


def safe_querymetadata(data: dict, original_header: dict, proj_name: str):
    print("proj_name: ", proj_name)
    for key, col in original_header.items():
        print("header: ", original_header[key])
        print("type: ", data["type"][key])
        print("child: ", data["child"][key])
        print("parent: ", data["parent"][key])
        print("mapping: ", data["mapping"][key])

        querymetadata = QueryMetaData()
        querymetadata.project_name = proj_name
        querymetadata.column_name = original_header[key]
        querymetadata.column_type = data["type"][key]
        querymetadata.column_category = data["parent"][key]
        querymetadata.column_subcategory = data["child"][key]
        querymetadata.column_URI = data["mapping"][key]

        querymetadata.save()
