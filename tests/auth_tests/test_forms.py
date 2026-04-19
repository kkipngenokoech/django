import pytest
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.test import TestCase


def test_issue_reproduction():
    """Test that UserChangeForm generates correct password reset link when accessed via to_field."""
    # Create a user instance
    user = User.objects.create_user(username='testuser', password='testpass123')
    
    # Create the form with the user instance
    form = UserChangeForm(instance=user)
    
    # Get the password field help text
    password_field = form.fields.get('password')
    help_text = password_field.help_text
    
    # The current buggy implementation uses '../password/' which breaks when accessed via to_field
    # The help text should contain a proper absolute path using the user's pk
    # Current code will have '../password/' but should have '../../{pk}/password/'
    assert '../password/' not in help_text, "Help text should not contain relative path '../password/'"
    assert f'../../{user.pk}/password/' in help_text, f"Help text should contain absolute path '../../{user.pk}/password/'"


class TestUserChangeFormPasswordLink(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
    
    def test_issue_reproduction(self):
        """Test that UserChangeForm generates correct password reset link when accessed via to_field."""
        form = UserChangeForm(instance=self.user)
        password_field = form.fields.get('password')
        help_text = password_field.help_text
        
        # This will fail with current buggy code that uses '../password/'
        assert '../password/' not in help_text
        assert f'../../{self.user.pk}/password/' in help_text