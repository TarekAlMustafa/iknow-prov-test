# Generated by Django 3.1.13 on 2022-09-21 14:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iknow_manager', '0003_headerclasses'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='HeaderClasses',
            new_name='HeaderClass',
        ),
    ]