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
