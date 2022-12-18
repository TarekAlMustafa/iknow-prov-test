# Generated by Django 3.1.13 on 2022-09-02 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Tool',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('repo_link', models.CharField(max_length=2048)),
                ('description', models.CharField(max_length=2048)),
                ('version', models.CharField(max_length=40)),
                ('versionDate', models.DateField()),
                ('implemented', models.BooleanField(default=False)),
                ('docker_image_name', models.CharField(max_length=4096)),
                ('docker_command', models.CharField(max_length=4096)),
                ('input_parameters', models.JSONField(default=dict)),
            ],
        ),
    ]
