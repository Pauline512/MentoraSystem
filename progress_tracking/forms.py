from django import forms
from django.contrib.auth import get_user_model # <--- CHANGED THIS LINE
from django.utils import timezone
from .models import Goal, ProgressEntry

# Get the currently active user model (which is your CustomUser)
User = get_user_model() # <--- ADDED THIS LINE


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['title', 'description', 'priority', 'target_date', 'mentor']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter goal title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your goal in detail'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'target_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'mentor': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter mentors to only show users in the Mentor group
        self.fields['mentor'].queryset = User.objects.filter(groups__name='Mentor')
        self.fields['mentor'].empty_label = "Select a mentor (optional)"

        # Set minimum date to today
        self.fields['target_date'].widget.attrs['min'] = timezone.now().date().isoformat()

    def clean_target_date(self):
        target_date = self.cleaned_data.get('target_date')
        if target_date and target_date < timezone.now().date():
            raise forms.ValidationError("Target date cannot be in the past.")
        return target_date


class ProgressEntryForm(forms.ModelForm):
    class Meta:
        model = ProgressEntry
        fields = ['goal', 'date', 'description', 'completion_percentage', 'notes']
        widgets = {
            'goal': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What progress was made?'
            }),
            'completion_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': 1
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            if user.groups.filter(name='Mentor').exists():
                # Mentors can add progress for their mentees' goals
                self.fields['goal'].queryset = Goal.objects.filter(mentor=user)
            else:
                # Mentees can add progress for their own goals
                self.fields['goal'].queryset = Goal.objects.filter(mentee=user)

        # Set default date to today
        self.fields['date'].initial = timezone.now().date()

        # Set max date to today
        self.fields['date'].widget.attrs['max'] = timezone.now().date().isoformat()

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise forms.ValidationError("Progress entry date cannot be in the future.")
        return date

    def clean_completion_percentage(self):
        percentage = self.cleaned_data.get('completion_percentage')
        if percentage is not None and (percentage < 0 or percentage > 100):
            raise forms.ValidationError("Completion percentage must be between 0 and 100.")
        return percentage


class GoalSearchForm(forms.Form):
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search goals...'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All')] + Goal.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    priority = forms.ChoiceField(
        choices=[('', 'All')] + Goal.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    def filter_goals(self, queryset):
        search = self.cleaned_data.get('search')
        status = self.cleaned_data.get('status')
        priority = self.cleaned_data.get('priority')

        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(description__icontains=search)
            )

        if status:
            queryset = queryset.filter(status=status)

        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset