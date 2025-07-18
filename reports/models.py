from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from mentorship.models import Session # Import Session model

class Report(models.Model):
    name = models.CharField(max_length=255)
    generated_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField()
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True) # Link to Session

    def __str__(self):
        return self.name