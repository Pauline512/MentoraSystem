from django.db import models

# Create your models here.
# APP 5: communication
# Handles the internal messaging system.
# =============================================================================

# Django imports
# -----------------------------
from django.db import models
from django.conf import settings
# Removed Mentorship import as it does not exist in mentorship.models
from django.contrib.auth.models import User

# Message and Notification models are already defined in mentorship/models.py
# and should be used from there if needed. Removing duplicates from here.