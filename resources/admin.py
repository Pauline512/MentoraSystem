from django.contrib import admin

# Register your models here.
# ------------------------
from django.contrib import admin
from .models import Resource

admin.site.register(Resource)