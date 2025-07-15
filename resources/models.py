from django.db import models

# Create your models here.
# APP 4: resources (Your Responsibility)
# Handles shared files and links.
# =============================================================================

# Django imports
# -------------------------
from django.db import models
from django.conf import settings

class Resource(models.Model):
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='resources/', null=True, blank=True)
    link = models.URLField(blank=True)
    download_count = models.IntegerField(default=0) # New field for download count
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title