from django.utils.translation import gettext_lazy as _
from django.db import models
from semantic_version import django_fields as semVer
import os

#todo add display name, add help, null/empty

class Dataset(models.Model):
    title =  models.CharField(max_length=500)
    description = models.CharField(max_length=1000)
    source = models.CharField(max_length=1000)
    contact = models.CharField(max_length=1000)
    link_metadata = models.CharField(max_length=1000)
    link_datasource = models.CharField(max_length=1000)
    show = models.BooleanField
    download = models.BooleanField
    viz =models.BooleanField

    def __str__(self):
        return self.title

def get_file_path(self, filename):
    return os.path.join('files', str(self.dataset.id), str(self.version), filename)

class Datastructure(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class DatastructureInline(models.Model):
    order = models.PositiveIntegerField(default=0)
    datastructure = models.ForeignKey(Datastructure, on_delete=models.CASCADE)
    short_name = models.CharField(max_length=100)
    name = models.CharField(max_length=500)
    description = models.CharField(max_length=1000)
    unit = models.CharField(max_length=50)
    datatype = models.CharField(max_length=50)
    show = models.BooleanField()
    download = models.BooleanField()
    viz = models.BooleanField()

class File(models.Model):
    file = models.FileField("File", upload_to=get_file_path)
    version = semVer.VersionField(coerce=True, max_length=30)
    date = models.DateField()
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    datastructure = models.ForeignKey(Datastructure, on_delete=models.DO_NOTHING, null=True)

    def file_name(self):
        return os.path.basename(self.file.name)

    def file_size(self):
        return self.file.__sizeof__()

    def __str__(self):
        return os.path.basename(self.file.name) + "("+ str(self.version) + ")"

    #todo get latest version for a dataset, get all ordered by version (-> view.py)
