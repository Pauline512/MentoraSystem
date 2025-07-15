from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from mentorship.models import Mentee, Mentor, MentorshipRequest # Import Mentee and Mentor models
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Goal, ProgressEntry, MentorshipSession
from .forms import GoalForm, ProgressEntryForm
from .serializers import GoalSerializer, ProgressEntrySerializer


class GoalListView(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'progress_tracking/goal_list.html'
    context_object_name = 'goals'
    paginate_by = 10
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Mentor').exists():
            # Mentors see goals of their mentees
            return Goal.objects.filter(mentor=user)
        else:
            # Mentees see their own goals
            return Goal.objects.filter(mentee=user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = 'mentor' if self.request.user.groups.filter(name='Mentor').exists() else 'mentee'
        return context


class GoalCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'progress_tracking/goal_form.html'
    success_url = reverse_lazy('progress_tracking:goal_list')

    def test_func(self):
        return hasattr(self.request.user, 'mentee')

    def form_valid(self, form):
        mentee_profile = self.request.user.mentee
        form.instance.mentee = mentee_profile.user

        # Attempt to find an accepted mentorship request to assign a mentor
        try:
            accepted_request = MentorshipRequest.objects.get(
                mentee=mentee_profile,
                status='ACCEPTED'
            )
            form.instance.mentor = accepted_request.mentor.user
        except MentorshipRequest.DoesNotExist:
            # If no accepted mentor, the mentor field will remain null (if allowed by model)
            messages.warning(self.request, "No accepted mentor found for this mentee. Goal created without an assigned mentor.")
        except MentorshipRequest.MultipleObjectsReturned:
            # Handle case where multiple accepted requests exist (shouldn't happen with unique constraint)
            messages.warning(self.request, "Multiple accepted mentors found. Assigning the first one.")
            accepted_request = MentorshipRequest.objects.filter(
                mentee=mentee_profile,
                status='ACCEPTED'
            ).first()
            form.instance.mentor = accepted_request.mentor.user

        messages.success(self.request, 'Goal created successfully!')
        return super().form_valid(form)


class GoalUpdateView(LoginRequiredMixin, UpdateView):
    model = Goal
    form_class = GoalForm
    template_name = 'progress_tracking/goal_form.html'
    success_url = reverse_lazy('progress_tracking:goal_list')
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Mentor').exists():
            return Goal.objects.filter(mentor=user)
        else:
            return Goal.objects.filter(mentee=user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Goal updated successfully!')
        return super().form_valid(form)


class GoalDeleteView(LoginRequiredMixin, DeleteView):
    model = Goal
    template_name = 'progress_tracking/goal_confirm_delete.html'
    success_url = reverse_lazy('progress_tracking:goal_list')
    
    def get_queryset(self):
        return Goal.objects.filter(mentee=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Goal deleted successfully!')
        return super().delete(request, *args, **kwargs)


class ProgressEntryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ProgressEntry
    form_class = ProgressEntryForm
    template_name = 'progress_tracking/progress_form.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'mentor')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        messages.success(self.request, 'Progress entry recorded successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('progress_tracking:dashboard')


class ProgressEntryDetailView(LoginRequiredMixin, DetailView):
    model = ProgressEntry
    template_name = 'progress_tracking/progress_detail.html'
    context_object_name = 'progress_entry'


@login_required
def dashboard_view(request):
    user = request.user
    context = {}
    
    if user.groups.filter(name='Mentor').exists():
        # Mentor dashboard
        mentee_goals = Goal.objects.filter(mentor=user)
        context.update({
            'user_role': 'mentor',
            'total_mentees': mentee_goals.values('mentee').distinct().count(),
            'active_goals': mentee_goals.filter(status='in_progress').count(),
            'completed_goals': mentee_goals.filter(status='completed').count(),
            'overdue_goals': [goal for goal in mentee_goals if goal.is_overdue],
            'recent_progress': ProgressEntry.objects.filter(goal__mentor=user)[:5],
            'goal_stats': mentee_goals.aggregate(
                avg_progress=Avg('progress_percentage'),
                total_goals=Count('id')
            )
        })
    else:
        # Mentee dashboard
        user_goals = Goal.objects.filter(mentee=user)
        context.update({
            'user_role': 'mentee',
            'total_goals': user_goals.count(),
            'active_goals': user_goals.filter(status='in_progress').count(),
            'completed_goals': user_goals.filter(status='completed').count(),
            'overdue_goals': [goal for goal in user_goals if goal.is_overdue],
            'recent_progress': ProgressEntry.objects.filter(goal__mentee=user)[:5],
            'goal_stats': user_goals.aggregate(
                avg_progress=Avg('progress_percentage'),
                total_goals=Count('id')
            )
        })
    
    return render(request, 'progress_tracking/dashboard.html', context)


@login_required
def goal_detail_view(request, pk):
    goal = get_object_or_404(Goal, pk=pk)
    
    # Check permissions
    if not (goal.mentee == request.user or goal.mentor == request.user):
        messages.error(request, 'You do not have permission to view this goal.')
        return redirect('progress_tracking:goal_list')
    
    progress_entries = goal.progress_entries.all()
    
    context = {
        'goal': goal,
        'progress_entries': progress_entries,
        'can_edit': goal.mentee == request.user or goal.mentor == request.user,
        'can_add_progress': True,  # Both mentors and mentees can add progress
    }
    
    return render(request, 'progress_tracking/goal_detail.html', context)


@login_required
def progress_chart_data(request, goal_id):
    """API endpoint for progress chart data"""
    goal = get_object_or_404(Goal, pk=goal_id)
    
    # Check permissions
    if not (goal.mentee == request.user or goal.mentor == request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    progress_entries = goal.progress_entries.all()
    
    data = {
        'labels': [entry.date.strftime('%Y-%m-%d') for entry in progress_entries],
        'progress': [entry.completion_percentage for entry in progress_entries],
        'goal_title': goal.title,
        'target_date': goal.target_date.strftime('%Y-%m-%d'),
        'current_progress': goal.progress_percentage
    }
    
    return JsonResponse(data)


# API ViewSets for REST endpoints
class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Mentor').exists():
            return Goal.objects.filter(mentor=user)
        else:
            return Goal.objects.filter(mentee=user)
    
    def perform_create(self, serializer):
        serializer.save(mentee=self.request.user)
    
    @action(detail=True, methods=['get'])
    def progress_history(self, request, pk=None):
        goal = self.get_object()
        progress_entries = goal.progress_entries.all()
        serializer = ProgressEntrySerializer(progress_entries, many=True)
        return Response(serializer.data)


class ProgressEntryViewSet(viewsets.ModelViewSet):
    serializer_class = ProgressEntrySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Mentor').exists():
            return ProgressEntry.objects.filter(goal__mentor=user)
        else:
            return ProgressEntry.objects.filter(goal__mentee=user)
    
    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)