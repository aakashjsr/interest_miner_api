from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(null=False, blank=False, unique=True)
    twitter_account_id = models.CharField(max_length=1024, null=True, blank=True)
    author_id = models.CharField(max_length=1024, null=True, blank=True)
