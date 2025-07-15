from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Goal(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
    ]
    
    mentee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='goals',
        limit_choices_to={'groups__name': 'Mentee'}
    )
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='mentee_goals',
        limit_choices_to={'groups__name': 'Mentor'},
        null=True, 
        blank=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='not_started')
    target_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    progress_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    class Meta:
        ordering = ['-target_date']
        verbose_name_plural = 'Goals'
        
    def __str__(self):
        return f"{self.title} - {self.mentee.username}"
    
    @property
    def is_overdue(self):
        return self.target_date < timezone.now().date() and self.status != 'completed'
    
    @property
    def days_remaining(self):
        delta = self.target_date - timezone.now().date()
        return delta.days


class ProgressEntry(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='progress_entries')
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    description = models.TextField()
    completion_percentage = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Progress Entries'
    
    def __str__(self):
        return f"{self.goal.title} - {self.date} ({self.completion_percentage}%)"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update goal progress percentage to match latest entry
        self.goal.progress_percentage = self.completion_percentage
        if self.completion_percentage == 100:
            self.goal.status = 'completed'
        elif self.completion_percentage > 0:
            self.goal.status = 'in_progress'
        self.goal.save()


class MentorshipSession(models.Model):
    """Model to track mentorship sessions for progress context"""
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='mentor_sessions'
    )
    mentee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='mentee_sessions'
    )
    date = models.DateTimeField()
    topic = models.CharField(max_length=200)
    duration = models.DurationField()
    notes = models.TextField(blank=True)
    goals_discussed = models.ManyToManyField(Goal, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Mentorship Session'
        verbose_name_plural = 'Mentorship Sessions'

    def __str__(self):
        return f"{self.mentor.username} - {self.mentee.username} ({self.date.date()})"