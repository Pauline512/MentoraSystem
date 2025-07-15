import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mywebsite.settings')
import django
django.setup()
from django.contrib.auth.models import User
User.objects.all().delete()
print('All user accounts have been deleted.')