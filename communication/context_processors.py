from .models import Notification

def unread_message_count(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_message_count': count}
    return {'unread_message_count': 0}
