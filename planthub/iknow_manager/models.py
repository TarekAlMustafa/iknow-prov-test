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


class HeaderClass(models.Model):
    main_category_label = models.CharField(max_length=4096)
    main_category_uri = models.CharField(max_length=4096)
    sub_category_label = models.CharField(max_length=4096)
    sub_category_uri = models.CharField(unique=True, max_length=4096)


class IknowEntity(models.Model):
    uri = models.CharField(max_length=10000, unique=True, null=True)
    label = models.CharField(max_length=4096, unique=True)


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
    """
    Creates a new entry of QueryMetaData for each column.
    """
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


def get_all_headerclasses():
    all_classes = {}
    c: HeaderClass
    for c in HeaderClass.objects.all():
        if c.main_category_label not in all_classes:
            all_classes[c.main_category_label] = []
        all_classes[c.main_category_label].append({
            'label': c.sub_category_label,
            'uri': c.sub_category_uri
        })

    return all_classes


def create_new_headerclass(data):
    # TODO: - validate form before saving new categories
    print("create_new_headerclass")
    print(data)
    if HeaderClass.objects.filter(sub_category_uri=data["newsuburi"]):
        return False

    header_class = HeaderClass()
    header_class.main_category_label = data["newmainlabel"]
    if "main_category_uri" in data:
        header_class.main_category_uri = data["newmainuri"]
    header_class.sub_category_label = data["newsublabel"]
    header_class.sub_category_uri = data["newsuburi"]

    header_class.save()


def get_entity_by_label():
    pass
