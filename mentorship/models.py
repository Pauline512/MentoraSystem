from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# --- 1. Interest Entity (Our "Skill Tag" blueprint) ---
# Expertise and Mentee Interests
class Interest(models.Model):
    name = models.CharField(max_length=100, unique=True) # e.g., "Software Engineering", "Product Management", "San Francisco"

    def __str__(self):
        return self.name

# --- 2. Mentee Entity (Our "Student Profile" blueprint) ---
class Mentee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=255, blank=True, null=True)
    interests = models.ManyToManyField(Interest, related_name='mentees', blank=True) # Mentees have interests (skill tags)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='mentee_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.username

# --- 3. Mentor Entity (Our "Expert Teacher Profile" blueprint) ---
class Mentor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=255, blank=True, null=True)
    # ManyToManyField for multiple expertise tags
    expertise = models.ManyToManyField(Interest, related_name='mentors', blank=True)

    # fields for the detailed mentor card 
    title = models.CharField(max_length=255, blank=True, null=True) 
    company = models.CharField(max_length=255, blank=True, null=True) 
    rating = models.DecimalField(max_digits=2, decimal_places=1, blank=True, null=True) 
    reviews_count = models.IntegerField(default=0) 
    price_per_session = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True) 
    experience_years = models.IntegerField(blank=True, null=True) 
    
    availability = models.CharField(max_length=255, blank=True, null=True)
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available for Mentorship'),
        ('BUSY', 'Currently Busy'),
        ('OFFLINE', 'Offline'),
    ]
    availability_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='AVAILABLE',
    )
    available_date=models.DateTimeField(blank=True, null=True)
    availabile_time=models.DateTimeField(blank=True, null=True)
    
    
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='mentor_pics/', blank=True, null=True)

    def __str__(self):
        # Display mentor by their full name if available, otherwise username
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username

# --- 4. MentorshipRequest Entity (Our "Mentorship Application Form" blueprint) ---
class MentorshipRequest(models.Model):
    mentee = models.ForeignKey(Mentee, on_delete=models.CASCADE, related_name='sent_requests')
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name='received_requests')
    request_date = models.DateTimeField(auto_now_add=True)
    message = models.TextField()

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING',
    )
    response_date = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    is_session_scheduled = models.BooleanField(default=False) 

    class Meta:
        unique_together = ('mentee', 'mentor', 'status')
        constraints = [
            models.UniqueConstraint(
                fields=['mentee', 'mentor'],
                condition=models.Q(status__in=['PENDING', 'ACCEPTED']),
                name='unique_pending_or_accepted_request'
            )
        ]

    def __str__(self):
        return f"Request from {self.mentee.user.username} to {self.mentor.user.username} ({self.status})"

# --- 5. Notification Entity (Our "Message Slip" blueprint) ---
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    TYPE_CHOICES = [
        ('NEW_REQUEST', 'New Mentorship Request'),
        ('REQUEST_ACCEPTED', 'Mentorship Request Accepted'),
        ('REQUEST_REJECTED', 'Mentorship Request Rejected'),
        ('GENERAL', 'General Message'),
    ]
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='GENERAL',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    related_request = models.ForeignKey(
        MentorshipRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message[:50]}..."
    
class Session(models.Model):
    # A session is linked to a specific mentorship request
    
    mentorship_request = models.ForeignKey(
        MentorshipRequest,
        on_delete=models.CASCADE, 
        related_name='sessions'
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    # Session Types 
    SESSION_TYPE_CHOICES = [
        ('PHONE_CALL', 'Phone Call'),
        ('VIDEO_CALL', 'Video Call'),
        ('CHAT', 'Chat'),
        ('IN_PERSON', 'In Person'),
    ]
    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPE_CHOICES,
        default='VIDEO_CALL', # default
        help_text="Type of mentorship session (e.g., Video Call, Phone Call)"
    )

    # Status of the session
    SESSION_STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('RESCHEDULED', 'Rescheduled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=SESSION_STATUS_CHOICES,
        default='SCHEDULED',
        help_text="Current status of the session"
    )

    location_details = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Details for the session location (e.g., Zoom link, phone number, address)"
    )
    notes = models.TextField(blank=True, null=True) # Notes about the session

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time'] # Order sessions by start time
        verbose_name = "Mentorship Session"
        verbose_name_plural = "Mentorship Sessions"

    def __str__(self):
        return f"Session for {self.mentorship_request.mentee.user.username} with {self.mentorship_request.mentor.user.username} on {self.start_time.strftime('%Y-%m-%d %H:%M')}"


# --- 7. Message Entity (Our "Letter" blueprint) ---
class Message(models.Model):
    # The sender of the message
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    # The recipient of the message
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')

    # The actual content of the message
    content = models.TextField()

    # Timestamp for when the message was sent
    timestamp = models.DateTimeField(auto_now_add=True)

    # To track if the message has been read by the recipient
    is_read = models.BooleanField(default=False)

    # Link to the related mentorship request
    mentorship_request = models.ForeignKey(
        MentorshipRequest,
        on_delete=models.CASCADE, 
        related_name='messages', # Allows request.messages.all()
        blank=True,
        null=True, # Allow messages not directly tied to a request initially, if needed
        help_text="The mentorship request this message pertains to."
    )

    class Meta:
        ordering = ['timestamp'] # Order messages by time
        verbose_name = "User Message"
        verbose_name_plural = "User Messages"

    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username}: {self.content[:50]}..."
