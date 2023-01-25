from rest_framework import serializers

from .models import Project, ProjectContact, ProjectFunFact


class ProjectContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectContact
        fields = ["id", "person_name", "person_email", "image"]


class ProjectFunFactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFunFact
        fields = ["position", "title_en", "title_de", "front_image", "back_image", "image_pair_name"]


class ProjectSerializer(serializers.ModelSerializer):
    contact = ProjectContactSerializer(many=True)
    funfacts = ProjectFunFactSerializer(many=True)

    class Meta:
        model = Project
        fields = ["id", "title_en", "title_de", "sub_title_en", "sub_title_de",
                  "description_en", "description_de", "logo", "link", "contact",
                  "funfacts"]
