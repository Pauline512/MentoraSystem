from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Avg
import csv
import json # Added for Chart.js data serialization
import io # Added for PDF generation

# For PDF generation
# You might need to install xhtml2pdf: pip install xhtml2pdf
from xhtml2pdf import pisa
from django.template.loader import get_template

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
def unified_report_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You are not authorized to view this report.")
        return redirect('home')

    # --- Data Collection for Report ---
    active_users = User.objects.filter(is_active=True).count()
    total_sessions = Session.objects.count()
    completed_sessions = Session.objects.filter(status='COMPLETED').count()
    all_sessions = Session.objects.all().select_related('mentorship_request__mentor', 'mentorship_request__mentee')
    feedback_entries = Report.objects.filter(name__startswith='Session Feedback').select_related('session__mentorship_request__mentor', 'session__mentorship_request__mentee')

    # Chart.js Data (Example - you'll need to populate this with real data)
    # For session trends, you might aggregate sessions by month/year
    session_trends_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    session_trends_data = [10, 15, 8, 12, 20, 18]

    # For mentor ratings, you might aggregate feedback ratings
    mentor_rating_labels = ["1 Star", "2 Stars", "3 Stars", "4 Stars", "5 Stars"]
    mentor_rating_data = [5, 10, 20, 30, 35]

    context = {
        'active_users': active_users,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'sessions': all_sessions,
        'feedback_entries': feedback_entries,
        'session_trends_labels': json.dumps(session_trends_labels),
        'session_trends_data': json.dumps(session_trends_data),
        'mentor_rating_labels': json.dumps(mentor_rating_labels),
        'mentor_rating_data': json.dumps(mentor_rating_data),
    }

    format_type = request.GET.get('format')

    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="unified_mentorship_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Active Users', active_users])
        writer.writerow(['Total Mentorship Sessions', total_sessions])
        writer.writerow(['Completed Sessions', completed_sessions])
        writer.writerow([])
        writer.writerow(['Mentorship Sessions Details'])
        writer.writerow(['Mentor', 'Mentee', 'Topic', 'Scheduled Time', 'Duration (minutes)', 'Status'])
        for session in all_sessions:
            writer.writerow([
                session.mentorship_request.mentor.user.username if hasattr(session.mentorship_request, 'mentor') and hasattr(session.mentorship_request.mentor, 'user') else 'N/A',
                session.mentorship_request.mentee.user.username if hasattr(session.mentorship_request, 'mentee') and hasattr(session.mentorship_request.mentee, 'user') else 'N/A',
                session.topic,
                session.start_time,
                int((session.end_time - session.start_time).total_seconds() / 60) if session.end_time and session.start_time else 'N/A',
                session.status
            ])
        writer.writerow([])
        writer.writerow(['Feedback Entries'])
        writer.writerow(['Mentor', 'Mentee', 'Mentor Rating', 'Mentee Rating', 'Comments'])
        for feedback in feedback_entries:
            writer.writerow([
                feedback.session.mentorship_request.mentor.user.username if hasattr(feedback.session, 'mentorship_request') and hasattr(feedback.session.mentorship_request, 'mentor') and hasattr(feedback.session.mentorship_request.mentor, 'user') else 'N/A',
                feedback.session.mentorship_request.mentee.user.username if hasattr(feedback.session, 'mentorship_request') and hasattr(feedback.session.mentorship_request, 'mentee') and hasattr(feedback.session.mentorship_request.mentee, 'user') else 'N/A',
                feedback.mentor_rating,
                feedback.mentee_rating,
                feedback.comments
            ])
        return response

    elif format_type == 'pdf':
        template_path = 'reports/report.html'
        template = get_template(template_path)
        html = template.render(context)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="unified_mentorship_report.pdf"'

        pisa_status = pisa.CreatePDF(
            html,                # the HTML to convert
            dest=response)       # file handle to receive result

        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response

    return render(request, 'reports/report.html', context)