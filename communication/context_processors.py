from mentorship.models import Notification # Corrected import path

def unread_message_count(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return {'unread_message_count': count}
    return {'unread_message_count': 0}
