from django.contrib import admin

from .models import Project, ProjectContact, ProjectFunFact


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "title_en", "title_de", "sub_title_en", "sub_title_de",
                    "description_en", "description_de", "logo", "link")


@admin.register(ProjectContact)
class ProjectContactAdmin(admin.ModelAdmin):
    fields = ('person_name', 'person_email', 'image')
    list_display = ("person_name", "person_email")

@admin.register(ProjectFunFact)
class ProjectFunFactsAdmin(admin.ModelAdmin):
    fields = ("position", "title_en", "title_de", "front_image", "back_image", "image_pair_name")
    list_display = ("position", "image_pair_name")
    ordering = ["position"]