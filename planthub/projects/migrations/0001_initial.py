# Generated by Django 3.1.13 on 2022-05-22 08:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectContact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('person_name', models.CharField(max_length=200, verbose_name='Name')),
                ('person_email', models.CharField(max_length=100, verbose_name='Email')),
                ('image', models.FileField(null=True, upload_to='person_images/', verbose_name='File')),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title_en', models.CharField(max_length=500, verbose_name='Title in English')),
                ('title_de', models.CharField(max_length=500, verbose_name='Title in German')),
                ('sub_title_en', models.CharField(max_length=500, verbose_name='Subtitle in English')),
                ('sub_title_de', models.CharField(max_length=500, verbose_name='Subtitle in German')),
                ('description_en', models.CharField(max_length=2000, verbose_name='Description in English')),
                ('description_de', models.CharField(max_length=2000, verbose_name='Description in German')),
                ('logo', models.FileField(upload_to='project_logos/', verbose_name='Project Logo')),
                ('link', models.CharField(max_length=1000, verbose_name='Project Website')),
                ('contact', models.ManyToManyField(blank=True, related_name='project_project_contacts', to='projects.ProjectContact', verbose_name='Project contacts')),
            ],
        ),
    ]
