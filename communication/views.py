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

@login_required
def message_thread(request, request_pk, recipient_pk):
    mentorship_request = get_object_or_404(MentorshipRequest, pk=request_pk)
    other_party = get_object_or_404(User, pk=recipient_pk)

    # Ensure the current user is part of this mentorship request
    if not (request.user == mentorship_request.mentee.user or request.user == mentorship_request.mentor.user):
        messages.error(request, "You are not authorized to view this conversation.")
        return redirect('communication:index')

    messages_in_thread = Message.objects.filter(
        mentorship_request=mentorship_request
    ).order_by('timestamp')

    # Mark messages sent to the current user as read
    messages_in_thread.filter(recipient=request.user, is_read=False).update(is_read=True)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                sender=request.user,
                recipient=other_party,
                content=content,
                mentorship_request=mentorship_request
            )
            # Optionally, create a notification for the recipient
            # Notification.objects.create(
            #     recipient=other_party,
            #     message=f"New message from {request.user.username}",
            #     notification_type='GENERAL',
            #     related_request=mentorship_request
            # )
            return redirect('communication:message_thread', request_pk=request_pk, recipient_pk=recipient_pk)
        else:
            messages.error(request, "Message content cannot be empty.")

    context = {
        'mentorship_request': mentorship_request,
        'other_party': other_party,
        'messages': messages_in_thread,
    }
    return render(request, 'communication/message_thread.html', context)
