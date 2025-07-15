from django.utils import timezone
from django.contrib import messages #for user feedback
from django.db import transaction # for atomic updates
from django.contrib.auth.decorators import login_required 
from .models import Mentor, Mentee, Interest,MentorshipRequest,Notification,Message, User, Session # Import Session model
from .forms import MentorshipRequestForm, MessageForm , SessionForm, UserRegistrationForm# Importing forms
from django.db.models import Q # for complex queries


from django.shortcuts import render, get_object_or_404,redirect # # render HTML templates, get entity objects, redirect user
from django.contrib.auth import login # Added for login functionality

def mentor_list(request):
    # Start with all mentors, and prefetch related user and expertise data for efficiency
    mentors = Mentor.objects.select_related('user').prefetch_related('expertise').all()

    # Get search and filter parameters from the URL (GET request)
    search_query = request.GET.get('q')
    filter_expertise = request.GET.get('expertise')
    filter_location = request.GET.get('location')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    #shall be enhanced to use date ranges
    available_date = request.GET.get('available_date') # For future date filtering
    available_time = request.GET.get('available_time') # For future time filtering

    # Applying search query (name, company)
    if search_query:
        mentors = mentors.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(company__icontains=search_query)
        ).distinct() # Use distinct to avoid duplicates if a mentor matches multiple search terms

    # Applying expertise filter 
    if filter_expertise:
        mentors = mentors.filter(expertise__name__iexact=filter_expertise).distinct()

    # Applying location filter
    if filter_location:
        mentors = mentors.filter(location__iexact=filter_location).distinct()

    # Applying price range filter
    if min_price:
        try:
            min_price = float(min_price)
            mentors = mentors.filter(price_per_session__gte=min_price)
        except ValueError:
            messages.error(request, "Invalid minimum price provided.")
    if max_price:
        try:
            max_price = float(max_price)
            mentors = mentors.filter(price_per_session__lte=max_price)
        except ValueError:
            messages.error(request, "Invalid maximum price provided.")

    # Apply availability filter (simplified shall be edited to fit for dates/times ranges as well)
    if available_date:
        mentors = mentors.filter(availability__icontains=available_date).distinct()
        messages.info(request, "Availability filtering by date is or placeholder.")
    if available_time:
        mentors = mentors.filter(availability__icontains=available_time).distinct()
        messages.info(request, "Availability filtering by time is our placeholder.")


    # Order the results 
    mentors = mentors.order_by('user__first_name', 'user__last_name')

    # Get distinct expertise and location options for sidebar filters
    all_expertise_options = Interest.objects.filter(mentors__isnull=False).distinct().order_by('name')
    all_location_options = Mentor.objects.values_list('location', flat=True).distinct().exclude(location__isnull=True).exclude(location='').order_by('location')


    context = {
        'mentors': mentors,
        'all_expertise_options': all_expertise_options,
        'all_location_options': all_location_options,
        # Pass back current query params making filter fields "sticky" in the search bar 
        'current_q': search_query or '',
        'current_expertise': filter_expertise or '',
        'current_location': filter_location or '',
        'current_min_price': request.GET.get('min_price', ''),
        'current_max_price': request.GET.get('max_price', ''),
        'current_available_date': request.GET.get('available_date', ''),
        'current_available_time': request.GET.get('available_time', ''),
    }
    return render(request, 'mentorship/mentor_list.html', context)


# it show details about a single mentor
def mentor_detail(request, pk): # <--- New view function
    mentor = get_object_or_404(Mentor, pk=pk)

    # Check if the logged-in user is a mentee and has a pending request with this mentor.
    mentee_has_pending_request = False
    if request.user.is_authenticated:
        try:
            mentee_profile = Mentee.objects.get(user=request.user)
            if MentorshipRequest.objects.filter(
                mentee=mentee_profile,
                mentor=mentor,
                status='PENDING'
            ).exists():# for just checking existence
                mentee_has_pending_request = True
        except Mentee.DoesNotExist:
            pass # User is logged in but not a mentee profile

    context = {
        'mentor': mentor,
        'mentee_has_pending_request': mentee_has_pending_request
    }
    return render(request, 'mentorship/mentor_detail.html', context)


# for requesting mentorship button
@login_required
def request_mentorship(request, mentor_pk):
    
    # First, finding the specific "Expert Teacher" this application is for.
    mentor = get_object_or_404(Mentor, pk=mentor_pk)

    # Getting the "Student Profile" of the person who is currently logged in.
    # If the logged-in user isn't a mentee, they can't send requests.
    try:
        mentee = request.user.mentee # Accessing the related Mentee object from the User
    except Mentee.DoesNotExist:
        messages.error(request, "You must have a mentee profile to send mentorship requests.")
        print("hello")
        return redirect('mentor_detail', pk=mentor_pk) # Redirect back to mentor detail page

    # checking If the student has already sent a PENDING application to this teacher, so we don't let them send another one. 
    existing_request = MentorshipRequest.objects.filter(
        mentee=mentee,
        mentor=mentor,
        status='PENDING'
    ).exists() # if we use .first(), gets the first one or None if not found

    if existing_request:
        print("hello")
        messages.info(request, f"You already have a PENDING request with {mentor.user.username}.")
        return redirect('mentor_detail', pk=mentor_pk)

    # If the student just filled out the form and clicked "Submit" (POST request)
    if request.method == 'POST':
        # taking the filled-out form.
        form = MentorshipRequestForm(request.POST) # Fill the form with submitted data
        if form.is_valid(): # Check if the form is filled out correctly
            #Create a new application form entry, but not saving it to the database yet with commit field set to false.
            mentorship_request = form.save(commit=False)
            # Attach the student's profile and the teacher's profile to the application.
            mentorship_request.mentee = mentee
            mentorship_request.mentor = mentor
            mentorship_request.status = 'PENDING' # Set initial status to PENDING
            mentorship_request.save() # Save the complete application form to the database!
            
            
           #creating a notification oject forthe mentor
            Notification.objects.create(
                recipient=mentor.user, # The mentor's User object is the recipient
                message=f"You have a new mentorship request from {mentee.user.username}!\n{mentorship_request.message[:20]}...",  
                notification_type='NEW_REQUEST',
                related_request=mentorship_request # Link to the newly created request
            )
            
            messages.success(request, f"Your mentorship request to {mentor.user.username} has been sent!")
            return redirect('mentor_detail', pk=mentor_pk) # Send student to the "mentor detail page)"
        else:
            # If the form has errors, tell the student to fix them.
            messages.error(request, "Please correct the errors in the form.")
    else:
        # If the student just arrived at the office (GET request), give them a blank form.
        form = MentorshipRequestForm()

    # Prepare the data for the "Application Form Page" (template).
    context = {
        'mentor': mentor,
        'form': form
    }
    # Rendering the "Application Form Page" for the student.
    return render(request, 'mentorship/request_mentorship.html', context)


# This view just opens the door to the Mentee Welcome Lobby.
def mentee_landing(request):
    return render(request, 'mentorship/mentee_landing.html')

def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            role = form.cleaned_data['role']
            if role == 'mentee':
                Mentee.objects.create(user=user)
            elif role == 'mentor':
                Mentor.objects.create(user=user)
            elif role == 'admin':
                user.is_staff = True
                user.is_superuser = True
                user.save()
            
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login') # Redirect to login page
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})



@login_required # Only logged-in users can see their notifications
def my_notifications(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    request_notifications = notifications.filter(notification_type__in=['NEW_REQUEST', 'REQUEST_ACCEPTED', 'REQUEST_REJECTED'])
    message_notifications = notifications.exclude(notification_type__in=['NEW_REQUEST', 'REQUEST_ACCEPTED', 'REQUEST_REJECTED'])

    # marking all UNREAD notifications as READ as soon as the uer clicks, my notifications button.
    # This updates the database in bulk, efficiently.
    unread_notifications = notifications.filter(is_read=False)
    if unread_notifications.exists(): # Only update if there are actual unread messages
        unread_notifications.update(is_read=True)
    context = {
        'request_notifications': request_notifications,
        'message_notifications': message_notifications,
    }
    return render(request, 'mentorship/my_notifications.html', context)

@login_required
def mentorship_request_detail(request, request_pk):
    mentorship_request = get_object_or_404(MentorshipRequest, pk=request_pk)
    # Ensure only the involved mentor/mentee can view this request
    if not (request.user == mentorship_request.mentee.user or request.user == mentorship_request.mentor.user):
        messages.error(request, "You are not authorized to view this mentorship request.")
        return redirect('dashboard_redirect') # Redirect to a safe page

    context = {
        'mentorship_request': mentorship_request
    }
    return render(request, 'mentorship/mentorship_request_detail.html', context)


@login_required
def mark_notification_read_and_redirect(request, notification_pk):
    notification = get_object_or_404(Notification, pk=notification_pk, recipient=request.user)
    notification.is_read = True
    notification.save()

    if notification.notification_type in ['NEW_REQUEST', 'REQUEST_ACCEPTED', 'REQUEST_REJECTED']:
        if notification.related_request:
            # For request-related notifications, redirect to the relevant request page or dashboard
            return redirect('mentorship_request_detail', request_pk=notification.related_request.pk)
        else:
            return redirect('my_notifications') # Fallback if related_request is missing
    else: # Assume it's a message notification or general notification
        if notification.related_request:
            # Redirect to the specific message thread if available
            other_user = None
            if request.user == notification.related_request.mentee.user:
                other_user = notification.related_request.mentor.user
            elif request.user == notification.related_request.mentor.user:
                other_user = notification.related_request.mentee.user
            
            if other_user:
                return redirect('message_thread', request_pk=notification.related_request.pk, recipient_pk=other_user.pk)
            else:
                return redirect('communication:index') # Fallback to general inbox
        else:
            return redirect('communication:index') # Fallback to general inbox
        
    
@login_required
@transaction.atomic 
def accept_request(request, request_pk):
    # Find the specific application form.
    mentorship_request = get_object_or_404(MentorshipRequest, pk=request_pk)

    # Checking if the person pressing the button is the actual teacher/expert/mentor for this application.
    if request.user != mentorship_request.mentor.user:
        messages.error(request, "You are not authorized to accept this request.")
        return redirect('my_notifications')

    # Check if there's already an ACCEPTED request for this mentee-mentor pair
    existing_accepted_request = MentorshipRequest.objects.filter(
        mentee=mentorship_request.mentee,
        mentor=mentorship_request.mentor,
        status='ACCEPTED'
    ).exists()

    if existing_accepted_request:
        messages.warning(request, f"There is already an ACCEPTED mentorship request for {mentorship_request.mentee.user.username} with {mentorship_request.mentor.user.username}.")
        return redirect('my_notifications')

    # Only accept if the application is currently PENDING.
    if mentorship_request.status == 'PENDING':
        mentorship_request.status = 'ACCEPTED'
        mentorship_request.response_date = timezone.now() # Mark response time
        mentorship_request.save()

        # Reject any other PENDING requests from the same mentee to the same mentor
        MentorshipRequest.objects.filter(
            mentee=mentorship_request.mentee,
            mentor=mentorship_request.mentor,
            status='PENDING'
        ).exclude(pk=mentorship_request.pk).update(
            status='REJECTED',
            response_date=timezone.now(),
            rejection_reason='Superseded by an accepted request.'
        )

        # Send a "Request Accepted" notification reply slip to the student.
        Notification.objects.create(
            recipient=mentorship_request.mentee.user,
            message=f"Your mentorship request to {mentorship_request.mentor.user.username} has been ACCEPTED!",
            notification_type='REQUEST_ACCEPTED',
            related_request=mentorship_request
        )
        # Notify the mentor that their request was accepted (if they initiated it)
        Notification.objects.create(
            recipient=mentorship_request.mentor.user,
            message=f"You have accepted the mentorship request from {mentorship_request.mentee.user.username}!",
            notification_type='REQUEST_ACCEPTED',
            related_request=mentorship_request
        )
        messages.success(request, f"Mentorship request from {mentorship_request.mentee.user.username} accepted.")
    else:
        messages.warning(request, "This request is not in a PENDING state and cannot be accepted.")

    return redirect('my_notifications') # Go back to notifications page

@login_required
@transaction.atomic
def decline_request(request, request_pk):
    # Find the specific application form.
    mentorship_request = get_object_or_404(MentorshipRequest, pk=request_pk)

    # ensure the user is the mentor for this request.
    if request.user != mentorship_request.mentor.user:
        messages.error(request, "You are not authorized to decline this request.")
        return redirect('my_notifications')

    # Only decline if the application is currently PENDING.
    if mentorship_request.status == 'PENDING':
        mentorship_request.status = 'REJECTED'
        mentorship_request.response_date = timezone.now() # Mark response time
        mentorship_request.save()

        # Reject any other PENDING requests from the same mentee to the same mentor
        MentorshipRequest.objects.filter(
            mentee=mentorship_request.mentee,
            mentor=mentorship_request.mentor,
            status='PENDING'
        ).exclude(pk=mentorship_request.pk).update(
            status='REJECTED',
            response_date=timezone.now(),
            rejection_reason='Another request was declined.'
        )

        # Send a "Request Rejected" notification reply slip to the student.
        Notification.objects.create(
            recipient=mentorship_request.mentee.user,
            message=f"Your mentorship request to {mentorship_request.mentor.user.username} has been REJECTED.",
            notification_type='REQUEST_REJECTED',
            related_request=mentorship_request
        )
        messages.success(request, f"Mentorship request from {mentorship_request.mentee.user.username} declined.")
    else:
        messages.warning(request, "This request is not in a PENDING state and cannot be declined.")

    return redirect('my_notifications') # Go back to notifications page




@login_required # Only logged-in users can view their sent requests
def my_requests(request):    
    is_mentor = False
    is_mentee = False
    requests = MentorshipRequest.objects.none() # Initialize requests to an empty queryset

    # Determine if the user is a mentor or mentee
    try:
        mentee_profile = Mentee.objects.get(user=request.user)
        is_mentee=True
        requests = MentorshipRequest.objects.filter(mentee=mentee_profile).order_by('-request_date')
    except Mentee.DoesNotExist:
        mentee_profile = None
    
    try:
        mentor_profile = Mentor.objects.get(user=request.user)
        is_mentor=True
        # If a user can be both mentee and mentor, you might need to combine querysets
        # For now, if they are a mentor, this will override mentee requests if both conditions are true
        requests = MentorshipRequest.objects.filter(mentor=mentor_profile).order_by('-request_date')  
    except Mentor.DoesNotExist:
        mentor_profile = None

    context = {
        'requests': requests,
        'is_mentor': is_mentor,
        'is_mentee': is_mentee,
    }
    return render(request, 'mentorship/my_requests.html', context)



@login_required # Only logged-in users can access their dashboard
def mentee_dashboard(request):
    user = request.user

    # Confirm the user has a "Student Profile" to access their dashboard.
    try:
        mentee_profile = Mentee.objects.get(user=user)
    except Mentee.DoesNotExist:
        messages.error(request, "You must have a mentee profile to view your dashboard.")
        return redirect('home') # Redirect if no mentee profile

    # Fetch all requests for the logged-in mentee and ordering them by request date
    all_requests = MentorshipRequest.objects.filter(mentee=mentee_profile).order_by('-request_date')

    # Calculating statistics
    total_requests_count = all_requests.count()
    pending_count = all_requests.filter(status='PENDING').count()
    accepted_count = all_requests.filter(status='ACCEPTED').count()
    rejected_count = all_requests.filter(status='REJECTED').count()

    success_rate = 0
    if total_requests_count > 0:
        success_rate = (accepted_count / total_requests_count) * 100

    # Filter requests for tabs (based on GET parameter)
    status_filter = request.GET.get('status', 'all') # Default to 'all'

    if status_filter == 'all':
        requests_for_display = all_requests
    else:
        requests_for_display = all_requests.filter(status=status_filter.upper())

    context = {
        'total_requests_count': total_requests_count,
        'pending_count': pending_count,
        'accepted_count': accepted_count,
        'rejected_count': rejected_count,
        'success_rate': round(success_rate), # Round to nearest whole number
        'requests': requests_for_display,
        'current_status_filter': status_filter, # Pass back for active tab styling
    }
    return render(request, 'mentorship/mentee_dashboard.html', context)



#scheduling sessions
@login_required
def schedule_session(request, request_pk):
    mentorship_request = get_object_or_404(MentorshipRequest, pk=request_pk)

    # Only the mentee who sent the request (or mentor who accepted it) can schedule
    if request.user != mentorship_request.mentee.user and \
       request.user != mentorship_request.mentor.user:
        messages.error(request, "You are not authorized to schedule a session for this request.")
        return redirect('mentee_dashboard') 

    # Only allow scheduling for ACCEPTED requests
    if mentorship_request.status != 'ACCEPTED':
        messages.warning(request, "A session can only be scheduled for an ACCEPTED mentorship request.")
        return redirect('mentee_dashboard')

    # If a session already exists for this request, redirect to its details or edit
    if mentorship_request.sessions.exists():
        messages.info(request, "A session for this request has already been scheduled.")
        # Redirect to session detail page
        return redirect('mentee_dashboard') # For now, redirect back

    # Placeholder for the actual scheduling form 
    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.mentorship_request = mentorship_request
            session.mentee = mentorship_request.mentee
            session.mentor = mentorship_request.mentor
            session.save()
            mentorship_request.is_session_scheduled = True # Update the flag on the request
            mentorship_request.save()
            
            messages.info(request, "notify user that the session has been scheduled for agiven request!")
            
            messages.success(request, "Session scheduled successfully!")
            return redirect('mentee_dashboard') # Or to a session detail page
        else:
            messages.error(request, "Please correct the errors in your message.")
        return redirect('mentee_dashboard')
    else:
        form = SessionForm()
        messages.info(request, "The scheduling page.")

    context = {
        'mentorship_request': mentorship_request,
    }
    return render(request, 'mentorship/schedule_session.html', context) # Render 

@login_required
def complete_session(request, session_pk):
    session = get_object_or_404(Session, pk=session_pk)

    # Ensure only the mentee or mentor involved in the session can mark it as complete
    if not (request.user == session.mentorship_request.mentee.user or request.user == session.mentorship_request.mentor.user):
        messages.error(request, "You are not authorized to complete this session.")
        return redirect('mentee_dashboard') # Redirect to a safe page

    if session.status != 'COMPLETED':
        session.status = 'COMPLETED'
        session.save()
        messages.success(request, "Session marked as completed. Please generate a report.")
    else:
        messages.info(request, "Session was already marked as completed.")

    return redirect('generate_session_report', session_pk=session.pk)

@login_required
def generate_session_report(request, session_pk):
    session = get_object_or_404(Session, pk=session_pk)

    # Ensure only participants can generate a report
    if not (request.user == session.mentorship_request.mentee.user or request.user == session.mentorship_request.mentor.user):
        messages.error(request, "You are not authorized to generate a report for this session.")
        return redirect('mentee_dashboard') # Redirect to a safe page

    if request.method == 'POST':
        form = SessionReportForm(request.POST)
        if form.is_valid():
            # Create a report entry
            report_data = {
                'session_id': session.pk,
                'mentee': session.mentorship_request.mentee.user.username,
                'mentor': session.mentorship_request.mentor.user.username,
                'session_type': session.session_type,
                'start_time': str(session.start_time), # Convert datetime to string for JSON
                'end_time': str(session.end_time), # Convert datetime to string for JSON
                'session_outcome': form.cleaned_data['session_outcome'],
                'key_takeaways': form.cleaned_data['key_takeaways'],
                'next_steps': form.cleaned_data['next_steps'],
                'rating': form.cleaned_data['rating'],
                'comments': form.cleaned_data['comments'], # New field
                'reported_by': request.user.username,
            }
            Report.objects.create(
                name=f"Session Report - {session.mentorship_request.mentee.user.username} & {session.mentorship_request.mentor.user.username} ({session.start_time.strftime('%Y-%m-%d')})",
                data=report_data,
                generated_by=request.user
            )
            messages.success(request, "Session report generated successfully!")
            return redirect('mentee_dashboard') # Redirect to dashboard after report
        else:
            messages.error(request, "Please correct the errors in the report form.")
    else:
        form = SessionReportForm()

    context = {
        'session': session,
        'form': form,
    }
    return render(request, 'mentorship/session_report_form.html', context)


#message chat
@login_required
def message_thread(request, request_pk, recipient_pk):
    current_user = request.user
    mentorship_request = get_object_or_404(MentorshipRequest, pk=request_pk)
    recipient_user = get_object_or_404(User, pk=recipient_pk)

    # Ensure the mentorship request is ACCEPTED before allowing messaging
    if mentorship_request.status != 'ACCEPTED':
        messages.error(request, "Messaging is only allowed for ACCEPTED mentorship requests.")
        return redirect('mentee_dashboard') # Or appropriate dashboard/requests page

    #Ensure current_user is part of this conversation. current_user is either the mentee or the mentor of this request, AND the recipient_user is the other party.
    is_mentee_of_request = (current_user == mentorship_request.mentee.user)
    is_mentor_of_request = (current_user == mentorship_request.mentor.user)

    if not (is_mentee_of_request or is_mentor_of_request):
        messages.error(request, "You are not authorized to view this message thread.")
        return redirect('mentee_dashboard') 

    # Determine if the recipient is the mentor or mentee of the request
    if (is_mentee_of_request and recipient_user != mentorship_request.mentor.user) or \
       (is_mentor_of_request and recipient_user != mentorship_request.mentee.user):
        messages.error(request, "Invalid recipient for this mentorship request.")
        return redirect('mentee_dashboard')

    # Fetch messages between current_user and recipient_user related to this request
    messages_in_thread = Message.objects.filter(
        mentorship_request=mentorship_request
    ).filter(
        Q(sender=current_user, recipient=recipient_user) |
        Q(sender=recipient_user, recipient=current_user)
    ).order_by('timestamp')

    # Mark messages sent by the recipient to the current user as read
    messages_in_thread.filter(recipient=current_user, is_read=False).update(is_read=True)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = current_user
            message.recipient = recipient_user
            message.mentorship_request = mentorship_request
            message.save()
            # Create notification for the recipient
            Notification.objects.create(
                recipient=recipient_user,
                message=f"You have received a message from {current_user.username}",
                notification_type='GENERAL', # Or a more specific type if available
                related_request=mentorship_request
            )
            messages.success(request, "Message sent!")
            # Redirecting to the same page to clear the form and show new message
            return redirect('message_thread', request_pk=request_pk, recipient_pk=recipient_pk)
        else:
            messages.error(request, "Please correct the errors in your message.")
    else:
        form = MessageForm()

    context = {
        'mentorship_request': mentorship_request,
        'recipient_user': recipient_user,
        'messages': messages_in_thread,
        'form': form,
        'current_user': current_user, # Pass current user for template logic ( message alignment)
    }
    return render(request, 'mentorship/message_thread.html', context)

@login_required
def dashboard_redirect(request):
    if hasattr(request.user, 'mentee'):
        return redirect('mentee_dashboard')
    elif hasattr(request.user, 'mentor'):
        return redirect('mentor_dashboard')
    elif request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')
    else:
        messages.warning(request, "Your account does not have an assigned role. Please contact support.")
        return redirect('home') # Fallback

@login_required
def mentor_dashboard(request):
    # Placeholder for mentor-specific logic
    return render(request, 'mentorship/mentor_dashboard.html', {'message': 'Welcome to your Mentor Dashboard!'})

@login_required
def admin_dashboard(request):
    # Placeholder for admin-specific logic
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "You are not authorized to view the admin dashboard.")
        return redirect('home')
    return render(request, 'mentorship/admin_dashboard.html', {'message': 'Welcome to your Admin Dashboard!'})

@login_required
def my_profile(request):
    user = request.user
    context = {
        'user_obj': user, # Renamed to avoid conflict with 'user' in template context
        'role': 'None',
    }

    if user.is_staff or user.is_superuser:
        context['role'] = 'Admin'
    elif hasattr(user, 'mentor'):
        context['role'] = 'Mentor'
        mentor_profile = user.mentor
        context['mentor_profile'] = mentor_profile
        context['pending_requests_count'] = MentorshipRequest.objects.filter(mentor=mentor_profile, status='PENDING').count()
        context['completed_sessions_count'] = Session.objects.filter(mentorship_request__mentor=mentor_profile, status='COMPLETED').count()
        context['mentees_interacted'] = MentorshipRequest.objects.filter(mentor=mentor_profile).values_list('mentee__user__username', flat=True).distinct()
    elif hasattr(user, 'mentee'):
        context['role'] = 'Mentee'
        mentee_profile = user.mentee
        context['mentee_profile'] = mentee_profile
        context['completed_sessions_count'] = Session.objects.filter(mentorship_request__mentee=mentee_profile, status='COMPLETED').count()
        context['mentors_interacted'] = MentorshipRequest.objects.filter(mentee=mentee_profile).values_list('mentor__user__username', flat=True).distinct()

    return render(request, 'mentorship/my_profile.html', context)