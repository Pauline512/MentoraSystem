from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from mentorship.models import Message, MentorshipRequest, Mentee, Mentor, User # Import necessary models
from django.db.models import Q

@login_required
def index(request):
    user = request.user
    conversations = []

    # Get mentorship requests where the user is the mentee
    mentee_requests = MentorshipRequest.objects.filter(mentee__user=user).select_related('mentor__user', 'mentee__user')
    for req in mentee_requests:
        conversations.append({
            'request': req,
            'other_party': req.mentor.user,
            'last_message': Message.objects.filter(mentorship_request=req).order_by('-timestamp').first()
        })

    # Get mentorship requests where the user is the mentor
    mentor_requests = MentorshipRequest.objects.filter(mentor__user=user).select_related('mentee__user', 'mentor__user')
    for req in mentor_requests:
        # Avoid adding duplicate conversations if the user is both mentee and mentor in different requests
        # Or if a request was already added from the mentee_requests query
        if not any(c['request'].pk == req.pk for c in conversations):
            conversations.append({
                'request': req,
                'other_party': req.mentee.user,
                'last_message': Message.objects.filter(mentorship_request=req).order_by('-timestamp').first()
            })

    # Sort conversations by the timestamp of the last message, or request date if no messages
    conversations.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else x['request'].request_date, reverse=True)

    return render(request, 'communication/message_list.html', {'conversations': conversations})
