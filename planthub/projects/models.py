from django.db import models
from django.utils.translation import gettext_lazy as _


# todo add display name, add help, null/empty
class ProjectContact(models.Model):
    person_name = models.CharField(_("Name"), max_length=200)
    person_email = models.CharField(_("Email"), max_length=100)
    image = models.FileField(_("File"), upload_to='images/person_images/', null=True)

    def __str__(self):
        return self.person_name


class ProjectFunFact(models.Model):
    image_pair_name = models.CharField(_("Name of Image Pair"), max_length=200)
    front_image = models.FileField(_("Front Image"), upload_to='images/funfacts/', null=True)
    back_image = models.FileField(_("Back Image"), upload_to='images/funfacts/', null=True)
    title_en = models.CharField(_("Imagetitle in English"), max_length=200)
    title_de = models.CharField(_("Imagetitle in German"), max_length=200)
    position = models.PositiveIntegerField("Position on Page", default=0,
                                           help_text="Here you can insert the position of the \
                                           image on the learn page. The higher the position number, \
                                           the further left the image will be on the page."
                                           )

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return self.image_pair_name


class Project(models.Model):
    title_en = models.CharField(_("Title in English"), max_length=500)
    title_de = models.CharField(_("Title in German"), max_length=500)
    sub_title_en = models.CharField(_("Subtitle in English"), max_length=500)
    sub_title_de = models.CharField(_("Subtitle in German"), max_length=500)
    description_en = models.CharField(_("Description in English"), max_length=2000)
    description_de = models.CharField(_("Description in German"), max_length=2000)
    logo = models.FileField(_("Project Logo"), upload_to='images/project_logos/')
    link = models.CharField(_("Project Website"), max_length=1000)
    contact = models.ManyToManyField(ProjectContact, related_name="project_project_contacts",
                                     blank=True, verbose_name=_("Project contacts"))
    funfacts = models.ManyToManyField(ProjectFunFact, related_name="project_project_funfacts",
                                      blank=True, verbose_name=_("Project funfacts"))

    def __str__(self):
        return self.title_en
