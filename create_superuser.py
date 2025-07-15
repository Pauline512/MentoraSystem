import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mywebsite.settings')
import django
django.setup()
from django.contrib.auth.models import User

username = 'admin'
email = 'admin@example.com'
password = 'adminpassword'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'Superuser {username} created successfully.')
else:
    print(f'Superuser {username} already exists.')