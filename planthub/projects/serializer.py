from rest_framework import serializers

from .models import Project, ProjectContact


class ProjectContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectContact
        fields = ["id", "person_name", "person_email", "image"]


class ProjectSerializer(serializers.ModelSerializer):
    contact = ProjectContactSerializer(many=True)

    class Meta:
        model = Project
        fields = ["id", "title_en", "title_de", "sub_title_en", "sub_title_de",
                  "description_en", "description_de", "logo", "link", "contact"]
