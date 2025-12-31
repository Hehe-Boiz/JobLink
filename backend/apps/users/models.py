from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField
from backend.apps.core.models import BaseModel

class User(AbstractUser, BaseModel):
    bio = models.TextField(blank=True, null=True)
    avatar = CloudinaryField(null=True)

    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

    @property
    def display_name(self):
        return self.name or self.username

