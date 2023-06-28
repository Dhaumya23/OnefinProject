import uuid

from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class Collections(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movies = models.JSONField()
    title = models.CharField(max_length=56)
    description = models.CharField(max_length=1000)
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
