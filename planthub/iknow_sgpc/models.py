# from django.conf import settings
from datetime import date

from django.db import models

from planthub.iknow_sgp.models import SGP

# Create your models here.

# https://www.tutorialspoint.com/adding-json-field-in-django-models
# https://riptutorial.com/django/example/30649/foreignkey
# https://stackoverflow.com/questions/34305805/foreignkey-user-in-models


class BioProject(models.Model):
    name = models.CharField(max_length=1023, unique=True, default='', blank=True, null=True)

    def get_all_project_names():
        info = [['--select one--']]

        distinct_names = BioProject.objects.values('name').distinct()

        for proj_name in distinct_names:
            info.append([proj_name['name']])

        return info

    def name_exists(name: str):
        for n in BioProject.objects.values('name'):
            if n['name'] == name:
                return True

        return False


class SGPC(models.Model):
    # name of this collection (user convenience when continuing work)
    collectionname = models.CharField(max_length=255, default='')

    # name of the associated biology research project (same for the associated sgps)
    bioprojectname = models.CharField(max_length=1023, default='')

    # description of the collection (user convenience)
    description = models.CharField(max_length=2000, default='')

    # all associated sgprojects (should be only assigned once and not changed afterwards)
    associated_sgprojects = models.ManyToManyField(SGP)

    cpaMappings = models.JSONField(default=dict)

    subclassMappings = models.JSONField(default=dict)

    collection_prov_rec = models.JSONField(default=dict)

    createdBy = models.CharField(max_length=255, default='')

    createdAt = models.DateField(default=date.today)

    class Meta:
        # Add verbose name
        verbose_name = 'SGPC (Subgraph Project Collection)'
        verbose_name_plural = 'SGPC (Subgraph Project Collections)'

# later for access control and displaying user specific database entries etc.
    # owningUser = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, default=1)

    def get_all_collection_names(self):
        info = [['--select one--']]

        collection_names = SGPC.objects.values('collectionname')

        for collection_name in collection_names:
            if collection_name["collectionname"] != "":
                info.append([collection_name['collectionname']])

        return info

    def get_property_uri(self, label=""):
        cpaMappingValues = self.cpaMappings.values()
        for cpaMap in cpaMappingValues:
            if label == cpaMap[3]:
                return cpaMap[2]

        return None

    # STEPS TO ADD A FIELD:

    # 1. add field here
    # add field in serializer
    # name field in frontend correctly
    # python manage.py makemigrations
    # python manage.py migrate
