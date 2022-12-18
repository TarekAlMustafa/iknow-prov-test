# This is meant to provide information about tools in our backend. It can be the basis for tools recommendation.
# Some of the information can should go to the provenance record (like an ID e.g., or unique tool name)
from django.db import models


class Tool(models.Model):
    #  General Info
    name = models.CharField(max_length=256)
    repo_link = models.CharField(max_length=2048)
    description = models.CharField(max_length=2048)
    version = models.CharField(max_length=40)
    versionDate = models.DateField()

    implemented = models.BooleanField(default=False)

    docker_image_name = models.CharField(max_length=4096)
    docker_command = models.CharField(max_length=4096)

    input_parameters = models.JSONField(default=dict)
