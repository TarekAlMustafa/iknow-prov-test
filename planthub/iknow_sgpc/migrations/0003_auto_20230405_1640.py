# Generated by Django 3.2.16 on 2023-04-05 14:40

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iknow_sgpc', '0002_sgpc_collection_prov_rec'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sgpc',
            options={'verbose_name': 'SGPC (Subgraph Project Collection)', 'verbose_name_plural': 'SGPC (Subgraph Project Collections)'},
        ),
        migrations.AddField(
            model_name='sgpc',
            name='createdAt',
            field=models.DateField(default=datetime.date.today),
        ),
        migrations.AddField(
            model_name='sgpc',
            name='createdBy',
            field=models.CharField(default='', max_length=255),
        ),
    ]
