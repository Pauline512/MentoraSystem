# notification_extras.py 
from django import template
from mentorship.models import Notification # Importig the Notification model

register = template.Library()

# the "mini-assistant" that runs for every page.
@register.inclusion_tag('mentorship/notification_badge.html', takes_context=True)
def notification_badge(context):
    request = context['request']
    if request.user.is_authenticated:
        # Checking the user's mailbox for any unread message slips.
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return {'unread_count': unread_count}
    return {'unread_count': 0} # Return 0 if not authenticated