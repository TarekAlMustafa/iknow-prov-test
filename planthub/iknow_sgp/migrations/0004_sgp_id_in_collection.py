# Generated by Django 3.1.13 on 2022-09-14 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iknow_sgp', '0003_auto_20220913_1057'),
    ]

    operations = [
        migrations.AddField(
            model_name='sgp',
            name='id_in_collection',
            field=models.IntegerField(default=0),
        ),
    ]
