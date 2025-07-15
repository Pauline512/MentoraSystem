from django import forms
from .models import MentorshipRequest,Message,Session, Mentee, Mentor
from django.contrib.auth.models import User

# This form is specifically for creating a MentorshipRequest form. forms.ModelForm (is a special type of form) that automatically builds itself based on a Django model (our MentorshipRequest blueprint).
class MentorshipRequestForm(forms.ModelForm):
    class Meta:
        model = MentorshipRequest # Telling Django: "This form is for the MentorshipRequest model."
        fields = ['message'] # Telling Django: "Only include the 'message' field from the model in this form."

        # customizing labels or add widgets for better HTML
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Tell your potential mentor why you want to connect...'}),
        }
        labels = {
            'message': 'Your Message to the Mentor',
        }
    
# This form is specifically for creating a Message chat form
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message here...'}),
        }


# This form is specifically for creating a session scheduling form
class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        # We'll let the view handle mentee, mentor, mentorship_request
        fields = ['start_time', 'end_time', 'session_type', 'location_details', 'notes']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),# 'datetime-local' is a modern HTML5 input type for date and time
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Any specific notes for this session?'}),
            'location_details': forms.TextInput(attrs={'placeholder': 'e.g., Zoom link, phone number, physical address'}),
        }
        # Adding labels for more user-friendly names than field names
        labels = {
            'start_time': 'Start Time',
            'end_time': 'End Time',
            'session_type': 'Session Type',
            'location_details': 'Location Details',
            'notes': 'Notes',
        }

    # Adding custom validations
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time.")
        return cleaned_data

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm password')

    ROLE_CHOICES = [
        ('mentee', 'Mentee'),
        ('mentor', 'Mentor'),
        ('admin', 'Admin'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class SessionReportForm(forms.Form):
    session_outcome = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label="Session Outcome/Summary")
    key_takeaways = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label="Key Takeaways for Mentee/Mentor")
    next_steps = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label="Next Steps/Action Items", required=False)
    rating = forms.IntegerField(label="Rating (1-5)", min_value=1, max_value=5)
    comments = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label="Comments about the session", required=False)
