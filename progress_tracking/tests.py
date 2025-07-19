from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from mentorship.models import Mentee, Mentor, MentorshipRequest
from progress_tracking.models import Goal
from django.utils import timezone
import datetime

class MentorGoalAccessTest(TestCase):
    def setUp(self):
        # Create groups
        self.mentor_group, _ = Group.objects.get_or_create(name='Mentor')
        self.mentee_group, _ = Group.objects.get_or_create(name='Mentee')

        # Create users
        self.mentor_user = User.objects.create_user(username='mentor1', password='password123')
        self.mentor_user.groups.add(self.mentor_group)
        self.mentor_profile = Mentor.objects.create(user=self.mentor_user)

        self.mentee_user_1 = User.objects.create_user(username='mentee1', password='password123')
        self.mentee_user_1.groups.add(self.mentee_group)
        self.mentee_profile_1 = Mentee.objects.create(user=self.mentee_user_1)

        self.mentee_user_2 = User.objects.create_user(username='mentee2', password='password123')
        self.mentee_user_2.groups.add(self.mentee_group)
        self.mentee_profile_2 = Mentee.objects.create(user=self.mentee_user_2)

        # Create an accepted mentorship request between mentor1 and mentee1
        self.accepted_request = MentorshipRequest.objects.create(
            mentee=self.mentee_profile_1,
            mentor=self.mentor_profile,
            status='ACCEPTED',
            message='Request 1',
            request_date=timezone.now()
        )

        # Create goals
        self.goal_mentee1 = Goal.objects.create(
            mentee=self.mentee_user_1,
            mentor=self.mentor_user,
            title='Mentee 1 Goal',
            description='Description for mentee 1 goal',
            target_date=timezone.now().date() + datetime.timedelta(days=30)
        )

        self.goal_mentee2 = Goal.objects.create(
            mentee=self.mentee_user_2,
            title='Mentee 2 Goal',
            description='Description for mentee 2 goal',
            target_date=timezone.now().date() + datetime.timedelta(days=30)
        )

        self.client = Client()

    def test_mentor_sees_only_accepted_mentee_goals_in_goal_list_view(self):
        self.client.login(username='mentor1', password='password123')
        response = self.client.get(reverse('progress_tracking:goal_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.goal_mentee1.title)
        self.assertNotContains(response, self.goal_mentee2.title)

    def test_mentor_sees_only_accepted_mentee_goals_in_dashboard_view(self):
        self.client.login(username='mentor1', password='password123')
        response = self.client.get(reverse('progress_tracking:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.goal_mentee1.title)
        self.assertNotContains(response, self.goal_mentee2.title)

    def test_mentee_sees_only_their_own_goals_in_goal_list_view(self):
        self.client.login(username='mentee1', password='password123')
        response = self.client.get(reverse('progress_tracking:goal_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.goal_mentee1.title)
        self.assertNotContains(response, self.goal_mentee2.title)

    def test_mentee_sees_only_their_own_goals_in_dashboard_view(self):
        self.client.login(username='mentee1', password='password123')
        response = self.client.get(reverse('progress_tracking:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.goal_mentee1.title)
        self.assertNotContains(response, self.goal_mentee2.title)
