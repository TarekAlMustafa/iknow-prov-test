from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField, ForeignKey
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Organization(models.Model):
    name = CharField(_("Name of Ogranization"), blank=True, max_length=255)

    def __str__(self):
        return self.name

class User(AbstractUser):
    """Default user for PlantHub."""

    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = CharField(_("First name"), blank=True, max_length=255)
    last_name = CharField(_("Last name"), blank=True, max_length=255)
    email = CharField(_("email"), blank=False, max_length=254, unique=True)
    status = CharField(_("Status of Member"), max_length=255, choices=(("stuff", "stuff"), ("student", "student")))
    organization = ForeignKey(Organization, verbose_name=_("Organization"), blank=True, null=True,
                              on_delete=models.DO_NOTHING)

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})
