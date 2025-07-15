from django.contrib import admin
from .models import Interest, Mentor, Mentee, MentorshipRequest, Notification, Session,Message,User # Ensure User is imported

admin.site.register(Interest)

class MentorAdmin(admin.ModelAdmin):
    list_display = ('user_full_name', 'title', 'company', 'location', 'rating', 'price_per_session', 'display_expertise')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'title', 'company', 'location', 'expertise__name')
    filter_horizontal = ('expertise',) #widget for ManyToManyField
    list_filter = ('location', 'expertise', 'availability_status') # Adding filters to admin sidebar

    fieldsets = ( # Organize fields into sections
        (None, {
            'fields': ('user', 'bio', 'profile_picture')
        }),
        ('Professional Details', {
            'fields': ('title', 'company', 'expertise', 'experience_years', 'rating', 'reviews_count', 'price_per_session', 'availability')
        }),
        ('Contact & Status', {
            'fields': ('location', 'availability_status')
        }),
    )

    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name and obj.user.last_name else obj.user.username
    user_full_name.short_description = 'Mentor Name'

    def display_expertise(self, obj):
        return ", ".join([interest.name for interest in obj.expertise.all()])
    display_expertise.short_description = 'Expertise'

class MenteeAdmin(admin.ModelAdmin):
    list_display = ('user_full_name', 'location', 'display_interests')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'location', 'interests__name')
    filter_horizontal = ('interests',)

    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name and obj.user.last_name else obj.user.username
    user_full_name.short_description = 'Mentee Name'

    def display_interests(self, obj):
        return ", ".join([interest.name for interest in obj.interests.all()])
    display_interests.short_description = 'Interests'
    
    
class MentorshipRequestAdmin(admin.ModelAdmin):
    list_display = ('mentee', 'mentor', 'status', 'request_date', 'response_date', 'is_session_scheduled')
    list_filter = ('status', 'is_session_scheduled')
    search_fields = ('mentee__user__username', 'mentor__user__username', 'message')
    fields = ('mentee', 'mentor', 'message', 'status', 'response_date', 'rejection_reason', 'is_session_scheduled')
   
    
class SessionAdmin(admin.ModelAdmin):
    list_display = ('mentorship_request','mentorship_request__mentee','mentorship_request__mentor','session_type', 'status', 'start_time', 'end_time')
    list_filter = ('session_type', 'status')
    search_fields = ('mentorship_request__mentee__user__username', 'mentorship_request__mentor__user__username', 'notes', 'location_details')
    # raw_id_fields = ('mentorship_request' ,'mentorship_request__mentee','mentorship_request__mentor') # Useful for selecting related objects
    fieldsets = (
        (None, {
            'fields': ('mentorship_request','mentorship_request__mentee','mentorship_request__mentor', 'session_type', 'status')
        }),
        ('Time & Location', {
            'fields': ('start_time', 'end_time', 'location_details')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
    
    
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'mentorship_request', 'timestamp', 'is_read', 'content_snippet')
    list_filter = ('is_read', 'timestamp', 'sender', 'recipient')
    search_fields = ('sender__username', 'recipient__username', 'content', 'mentorship_request__id')
    raw_id_fields = ('sender', 'recipient', 'mentorship_request') # Useful for selecting related objects

    def content_snippet(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    content_snippet.short_description = 'Content'

admin.site.register(Message, MessageAdmin) 


admin.site.register(Session, SessionAdmin)    


admin.site.register(Mentor, MentorAdmin)
admin.site.register(Mentee, MenteeAdmin)
admin.site.register(MentorshipRequest)
admin.site.register(Notification)