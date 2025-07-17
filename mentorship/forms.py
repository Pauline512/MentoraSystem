from django import forms
from .models import MentorshipRequest,Message,Session, Mentee, Mentor, Feedback, MentorEvaluation
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

# New: MenteeRegistrationForm
class MenteeRegistrationForm(forms.ModelForm):
    class Meta:
        model = Mentee
        fields = ['profile_picture', 'contact', 'location', 'bio', 'interests']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell us about yourself...'}),
            'interests': forms.CheckboxSelectMultiple,
        }

# New: MentorRegistrationForm
class MentorRegistrationForm(forms.ModelForm):
    class Meta:
        model = Mentor
        fields = ['profile_picture', 'contact', 'location', 'bio', 'expertise', 'title', 'company', 'experience_years']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell us about your expertise...'}),
            'expertise': forms.CheckboxSelectMultiple,
        }

class SessionReportForm(forms.Form):
    session_outcome = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label="Session Outcome/Summary")
    key_takeaways = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label="Key Takeaways for Mentee/Mentor")
    next_steps = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label="Next Steps/Action Items", required=False)
    rating = forms.IntegerField(label="Rating (1-5)", min_value=1, max_value=5)
    comments = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label="Comments about the session", required=False)

class UserProfileUpdateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False, label='New password')
    password2 = forms.CharField(widget=forms.PasswordInput, required=False, label='Confirm new password')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        if password or password2:
            if password != password2:
                raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = [
            'session_rating',
            'content_clarity',
            'relevance',
            'structure',
            'mentor_support',
            'mentor_listening',
            'mentor_knowledge',
            'mentor_rating',
            'learning',
            'expectations_met',
            'expectations_explanation',
        ]
        widgets = {
            'session_rating': forms.RadioSelect,
            'content_clarity': forms.RadioSelect,
            'relevance': forms.RadioSelect,
            'structure': forms.RadioSelect,
            'mentor_support': forms.RadioSelect,
            'mentor_listening': forms.RadioSelect,
            'mentor_knowledge': forms.RadioSelect,
            'mentor_rating': forms.RadioSelect,
            'learning': forms.Textarea(attrs={'rows': 3, 'placeholder': 'What did you learn or gain from this session?'}),
            'expectations_met': forms.RadioSelect,
            'expectations_explanation': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Were your expectations met? Why or why not?'}),
        }
        labels = {
            'session_rating': 'Overall Session Rating (1–5)',
            'content_clarity': 'Was the session content clear and understandable?',
            'relevance': 'Was the session relevant to your goals or challenges?',
            'structure': 'Was the session well-structured and organized?',
            'mentor_support': 'Was the mentor supportive and approachable?',
            'mentor_listening': 'Did the mentor actively listen and respond to your questions?',
            'mentor_knowledge': 'Was the mentor knowledgeable about the subject?',
            'mentor_rating': 'Rate your overall satisfaction with your mentor (1–5)',
            'learning': 'What did you learn or gain from this session?',
            'expectations_met': 'Were your expectations met?',
            'expectations_explanation': 'Why or why not?',
        }

class MentorEvaluationForm(forms.ModelForm):
    class Meta:
        model = MentorEvaluation
        fields = [
            'evaluation_date',
            'punctuality',
            'preparedness',
            'participation',
            'responsiveness',
            'initiative',
            'initiative_comment',
            'progress',
            'improvement_since_last',
            'key_skills',
            'challenges',
            'tasks_completed',
            'tasks_comment',
            'strengths',
            'areas_for_improvement',
            'overall_evaluation',
            'recommend_advanced',
            'recommend_comment',
        ]
        widgets = {
            'evaluation_date': forms.DateInput(attrs={'type': 'date'}),
            'punctuality': forms.Select,
            'preparedness': forms.Select,
            'participation': forms.Select,
            'responsiveness': forms.Select,
            'initiative': forms.Select,
            'initiative_comment': forms.Textarea(attrs={'rows': 2}),
            'progress': forms.Select,
            'improvement_since_last': forms.Textarea(attrs={'rows': 2}),
            'key_skills': forms.Textarea(attrs={'rows': 2}),
            'challenges': forms.Textarea(attrs={'rows': 2}),
            'tasks_completed': forms.Select,
            'tasks_comment': forms.Textarea(attrs={'rows': 2}),
            'strengths': forms.Textarea(attrs={'rows': 2}),
            'areas_for_improvement': forms.Textarea(attrs={'rows': 2}),
            'overall_evaluation': forms.Select,
            'recommend_advanced': forms.Select,
            'recommend_comment': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'evaluation_date': 'Session Date',
            'punctuality': 'Punctuality and Attendance',
            'preparedness': 'Preparedness for the Session',
            'participation': 'Participation Level',
            'responsiveness': 'Responsiveness to Feedback',
            'initiative': 'Initiative & Proactiveness',
            'initiative_comment': 'Comment on Initiative/Proactiveness',
            'progress': 'Progress Toward Agreed Goals',
            'improvement_since_last': 'Improvement Since Last Session',
            'key_skills': 'Key Skills or Knowledge Demonstrated',
            'challenges': 'Challenges Observed',
            'tasks_completed': 'Has the mentee completed agreed tasks or milestones?',
            'tasks_comment': 'Explanation for Tasks/Milestones',
            'strengths': 'Strengths Noted',
            'areas_for_improvement': 'Areas for Improvement',
            'overall_evaluation': 'Overall Evaluation of Mentee',
            'recommend_advanced': 'Would you recommend this mentee for advanced opportunities or responsibilities?',
            'recommend_comment': 'Justification for Recommendation',
        }
