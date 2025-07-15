import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mywebsite.settings')
import django
django.setup()
from reports.models import Report
from django.contrib.auth.models import User
from django.utils import timezone

# Get an admin user (or create one if none exists)
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    admin_user = User.objects.create_superuser('testadmin', 'testadmin@example.com', 'testpassword')
    print("Created a test admin user: testadmin/testpassword")

# Create a sample report
report_name = "Sample Mentorship Activity Report"
report_data = {
    "total_mentors": 10,
    "total_mentees": 25,
    "accepted_requests": 15,
    "pending_requests": 5,
    "completed_sessions": 8,
    "top_mentor": {"username": "mentor1", "sessions": 3},
    "recent_activity": [
        {"type": "request", "user": "mentee_alpha", "date": "2025-07-14"},
        {"type": "session", "user": "mentor_beta", "date": "2025-07-13"}
    ]
}

if not Report.objects.filter(name=report_name).exists():
    Report.objects.create(
        name=report_name,
        data=report_data,
        generated_by=admin_user,
        generated_at=timezone.now()
    )
    print(f"Sample report '{report_name}' created successfully.")
else:
    print(f"Sample report '{report_name}' already exists.")
