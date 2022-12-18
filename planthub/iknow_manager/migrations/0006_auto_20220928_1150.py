# Generated by Django 3.1.13 on 2022-09-28 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iknow_manager', '0005_iknowentity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='iknowentity',
            name='label',
            field=models.CharField(max_length=4096, unique=True),
        ),
        migrations.AlterField(
            model_name='iknowentity',
            name='uri_number',
            field=models.CharField(max_length=1024, unique=True),
        ),
    ]