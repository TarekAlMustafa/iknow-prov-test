# from django.conf import settings
from django.db import models

from planthub.iknow_datasets.models import Dataset

# https://www.tutorialspoint.com/adding-json-field-in-django-models
# https://riptutorial.com/django/example/30649/foreignkey
# https://stackoverflow.com/questions/34305805/foreignkey-user-in-models

BIOPROJECTNAME_CHOICES = [
    ('PhenObs', 'Phenobs'),
    ('Glonaf', 'Glonaf'),
    ('sPlot', 'sPlot')
]


class SGP(models.Model):
    # name of the associated biology research project
    bioprojectname = models.CharField(max_length=255, choices=BIOPROJECTNAME_CHOICES, default='PhenObs')

    # the dataset source dataset for this SGP (the initial dataset to work with)
    source_dataset = models.ManyToManyField(Dataset)

    # record of provenance of generated files
    # TODO: - mark layout as comment here
    provenanceRecord = models.JSONField(default=dict)

    cpaMappings = models.JSONField(default=dict)

    original_table_header = models.JSONField(default=dict)

    original_filename = models.CharField(max_length=4096, default="")

    project_copied = models.BooleanField(default=False)

    datasets_copied = models.BooleanField(default=False)

    id_in_collection = models.IntegerField(default=0)

    # later for access control and displaying user specific database entries etc.
    # owningUser = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, default=1)
