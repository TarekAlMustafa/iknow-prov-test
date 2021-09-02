# Generated by Django 3.1.13 on 2021-09-01 21:00

from planthub.datasets.models import *
from django.db import migrations, models
import django.db.models.deletion
import semantic_version.django_fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500)),
                ('description', models.CharField(max_length=1000)),
                ('source', models.CharField(max_length=1000)),
                ('contact', models.CharField(max_length=1000)),
                ('link_metadata', models.CharField(max_length=1000)),
                ('link_datasource', models.CharField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='Datastructure',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=get_file_path, verbose_name='File')),
                ('version', semantic_version.django_fields.VersionField(coerce=True, max_length=30, partial=False)),
                ('date', models.DateField()),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datasets.dataset')),
                ('datastructure', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='datasets.datastructure')),
            ],
        ),
        migrations.CreateModel(
            name='DatastructureInline',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(default=0)),
                ('short_name', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=500)),
                ('description', models.CharField(max_length=1000)),
                ('unit', models.CharField(max_length=50)),
                ('datatype', models.CharField(max_length=50)),
                ('show', models.BooleanField()),
                ('download', models.BooleanField()),
                ('viz', models.BooleanField()),
                ('datastructure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datasets.datastructure')),
            ],
        ),
    ]
