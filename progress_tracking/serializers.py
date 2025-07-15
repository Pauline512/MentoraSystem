from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Goal, ProgressEntry, MentorshipSession


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class GoalSerializer(serializers.ModelSerializer):
    mentee = UserSerializer(read_only=True)
    mentor = UserSerializer(read_only=True)
    mentor_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    is_overdue = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = Goal
        fields = [
            'id', 'title', 'description', 'priority', 'status', 
            'target_date', 'created_at', 'updated_at', 'progress_percentage',
            'mentee', 'mentor', 'mentor_id', 'is_overdue', 'days_remaining'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'progress_percentage']
    
    def validate_mentor_id(self, value):
        if value is not None:
            try:
                mentor = User.objects.get(id=value, groups__name='Mentor')
                return value
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid mentor ID or user is not a mentor.")
        return value
    
    def validate_target_date(self, value):
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Target date cannot be in the past.")
        return value
    
    def create(self, validated_data):
        mentor_id = validated_data.pop('mentor_id', None)
        if mentor_id:
            validated_data['mentor'] = User.objects.get(id=mentor_id)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        mentor_id = validated_data.pop('mentor_id', None)
        if mentor_id:
            validated_data['mentor'] = User.objects.get(id=mentor_id)
        return super().update(instance, validated_data)


class ProgressEntrySerializer(serializers.ModelSerializer):
    recorded_by = UserSerializer(read_only=True)
    goal = GoalSerializer(read_only=True)
    goal_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ProgressEntry
        fields = [
            'id', 'goal', 'goal_id', 'recorded_by', 'date', 
            'description', 'completion_percentage', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_goal_id(self, value):
        user = self.context['request'].user
        try:
            if user.groups.filter(name='Mentor').exists():
                # Mentors can add progress for their mentees' goals
                goal = Goal.objects.get(id=value, mentor=user)
            else:
                # Mentees can add progress for their own goals
                goal = Goal.objects.get(id=value, mentee=user)
            return value
        except Goal.DoesNotExist:
            raise serializers.ValidationError("Invalid goal ID or you don't have permission to access this goal.")
    
    def validate_completion_percentage(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Completion percentage must be between 0 and 100.")
        return value
    
    def validate_date(self, value):
        from django.utils import timezone
        if value > timezone.now().date():
            raise serializers.ValidationError("Progress entry date cannot be in the future.")
        return value
    
    def create(self, validated_data):
        goal_id = validated_data.pop('goal_id')
        validated_data['goal'] = Goal.objects.get(id=goal_id)
        return super().create(validated_data)


class MentorshipSessionSerializer(serializers.ModelSerializer):
    mentor = UserSerializer(read_only=True)
    mentee = UserSerializer(read_only=True)
    goals_discussed = GoalSerializer(many=True, read_only=True)
    goals_discussed_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = MentorshipSession
        fields = [
            'id', 'mentor', 'mentee', 'date', 'topic', 'duration', 
            'notes', 'goals_discussed', 'goals_discussed_ids', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        goals_discussed_ids = validated_data.pop('goals_discussed_ids', [])
        session = super().create(validated_data)
        if goals_discussed_ids:
            session.goals_discussed.set(goals_discussed_ids)
        return session
    
    def update(self, instance, validated_data):
        goals_discussed_ids = validated_data.pop('goals_discussed_ids', None)
        session = super().update(instance, validated_data)
        if goals_discussed_ids is not None:
            session.goals_discussed.set(goals_discussed_ids)
        return session


class GoalProgressSummarySerializer(serializers.Serializer):
    """Serializer for goal progress summary data"""
    goal_id = serializers.IntegerField()
    goal_title = serializers.CharField()
    current_progress = serializers.IntegerField()
    target_date = serializers.DateField()
    is_overdue = serializers.BooleanField()
    days_remaining = serializers.IntegerField()
    total_entries = serializers.IntegerField()
    last_updated = serializers.DateTimeField()


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_goals = serializers.IntegerField()
    active_goals = serializers.IntegerField()
    completed_goals = serializers.IntegerField()
    overdue_goals = serializers.IntegerField()
    average_progress = serializers.FloatField()
    total_progress_entries = serializers.IntegerField()