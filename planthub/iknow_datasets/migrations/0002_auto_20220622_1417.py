# Generated by Django 3.1.13 on 2022-06-22 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iknow_datasets', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='file_field',
            field=models.FileField(upload_to='iknow_datasets'),
        ),
    ]
