from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Report(models.Model):
    name = models.CharField(max_length=255)
    generated_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField()
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name