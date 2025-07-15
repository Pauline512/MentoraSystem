from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Goal, ProgressEntry, MentorshipSession


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'mentee', 'mentor', 'priority', 'status', 
        'progress_percentage', 'target_date', 'is_overdue_display', 'created_at'
    ]
    list_filter = ['status', 'priority', 'created_at', 'target_date']
    search_fields = ['title', 'description', 'mentee__username', 'mentor__username']
    readonly_fields = ['progress_percentage', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'mentee', 'mentor')
        }),
        ('Goal Settings', {
            'fields': ('priority', 'status', 'target_date', 'progress_percentage')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">Overdue</span>')
        return format_html('<span style="color: green;">On Track</span>')
    is_overdue_display.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('mentee', 'mentor')


class ProgressEntryInline(admin.TabularInline):
    model = ProgressEntry
    extra = 0
    readonly_fields = ['created_at']
    fields = ['date', 'recorded_by', 'completion_percentage', 'description', 'created_at']


@admin.register(ProgressEntry)
class ProgressEntryAdmin(admin.ModelAdmin):
    list_display = [
        'goal', 'recorded_by', 'date', 'completion_percentage', 
        'progress_bar', 'created_at'
    ]
    list_filter = ['date', 'created_at', 'goal__status']
    search_fields = ['goal__title', 'description', 'recorded_by__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Progress Information', {
            'fields': ('goal', 'recorded_by', 'date', 'completion_percentage')
        }),
        ('Details', {
            'fields': ('description', 'notes')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def progress_bar(self, obj):
        percentage = obj.completion_percentage
        color = 'green' if percentage >= 75 else 'orange' if percentage >= 50 else 'red'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; line-height: 20px; color: white; font-size: 12px;">{}</div>'
            '</div>',
            percentage, color, f'{percentage}%'
        )
    progress_bar.short_description = 'Progress'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('goal', 'recorded_by')


@admin.register(MentorshipSession)
class MentorshipSessionAdmin(admin.ModelAdmin):
    list_display = [
        'mentor', 'mentee', 'date', 'topic', 'duration', 
        'goals_count', 'created_at'
    ]
    list_filter = ['date', 'created_at']
    search_fields = ['mentor__username', 'mentee__username', 'topic', 'notes']
    readonly_fields = ['created_at']
    filter_horizontal = ['goals_discussed']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('mentor', 'mentee', 'date', 'topic', 'duration')
        }),
        ('Content', {
            'fields': ('notes', 'goals_discussed')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def goals_count(self, obj):
        count = obj.goals_discussed.count()
        if count > 0:
            return format_html(
                '<a href="{}?goals_discussed__id__exact={}">{} goals</a>',
                reverse('admin:progress_tracking_goal_changelist'),
                obj.id,
                count
            )
        return '0 goals'
    goals_count.short_description = 'Goals Discussed'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('mentor', 'mentee').prefetch_related('goals_discussed')


# Custom admin actions
@admin.action(description='Mark selected goals as completed')
def mark_goals_completed(modeladmin, request, queryset):
    queryset.update(status='completed', progress_percentage=100)


@admin.action(description='Mark selected goals as in progress')
def mark_goals_in_progress(modeladmin, request, queryset):
    queryset.update(status='in_progress')


# Add actions to GoalAdmin
GoalAdmin.actions = [mark_goals_completed, mark_goals_in_progress]


# Admin site customization
admin.site.site_header = 'Mentorship Progress Tracking Admin'
admin.site.site_title = 'Progress Tracking Admin'
admin.site.index_title = 'Welcome to Progress Tracking Administration'