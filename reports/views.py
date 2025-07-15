from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Avg
import csv

from .models import Report
from mentorship.models import Mentee, Mentor, Session, User, MentorshipRequest # Import necessary models

@login_required
def index(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You are not authorized to view reports.")
        return redirect('home')

    reports = Report.objects.all().order_by('-generated_at')
    return render(request, 'reports/index.html', {'reports': reports})

@login_required
def download_mentorship_report_csv(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You are not authorized to download this report.")
        return redirect('home')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="mentorship_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Metric', 'Value'])

    # Number of mentorship sessions (completed or scheduled)
    total_sessions = Session.objects.count()
    writer.writerow(['Total Mentorship Sessions', total_sessions])

    # Active Users
    total_users = User.objects.count()
    total_mentees = Mentee.objects.count()
    total_mentors = Mentor.objects.count()
    writer.writerow(['Total Users', total_users])
    writer.writerow(['Total Mentees', total_mentees])
    writer.writerow(['Total Mentors', total_mentors])

    # List of active users with roles
    writer.writerow([]) # Empty row for separation
    writer.writerow(['Active Users Details', ''])
    writer.writerow(['Username', 'Role'])
    for user in User.objects.all().order_by('username'):
        role = 'None'
        if user.is_superuser or user.is_staff:
            role = 'Admin'
        elif hasattr(user, 'mentee'):
            role = 'Mentee'
        elif hasattr(user, 'mentor'):
            role = 'Mentor'
        writer.writerow([user.username, role])

    # Completed Sessions
    completed_sessions = Session.objects.filter(status='COMPLETED').count()
    writer.writerow([])
    writer.writerow(['Completed Sessions', completed_sessions])

    # Feedback Ratings
    # Assuming 'rating' and 'comments' are stored in the 'data' JSONField of the Report model
    session_reports = Report.objects.filter(name__startswith='Session Report')
    average_rating = session_reports.aggregate(Avg('data__rating'))['data__rating__avg']
    
    writer.writerow([])
    writer.writerow(['Average Session Rating', f'{average_rating:.2f}' if average_rating else 'N/A'])

    writer.writerow([])
    writer.writerow(['Individual Session Feedback', '', ''])
    writer.writerow(['Session ID', 'Rating', 'Comments'])
    for report in session_reports:
        session_id = report.data.get('session_id', 'N/A')
        rating = report.data.get('rating', 'N/A')
        comments = report.data.get('comments', 'N/A')
        writer.writerow([session_id, rating, comments])

    return response