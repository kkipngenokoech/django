import pytest
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.test import TestCase


def test_issue_reproduction():
    """Test that password reset tokens are invalidated when user email changes."""
    User = get_user_model()
    
    # Create a user with an email
    user = User.objects.create_user(
        username='testuser',
        email='original@example.com',
        password='testpass123'
    )
    
    # Generate a password reset token
    token = default_token_generator.make_token(user)
    
    # Verify the token is valid
    assert default_token_generator.check_token(user, token) is True
    
    # Change the user's email address
    user.email = 'changed@example.com'
    user.save()
    
    # The token should now be invalid, but currently it remains valid (this is the bug)
    # This assertion will FAIL on the current buggy code because the token remains valid
    assert default_token_generator.check_token(user, token) is False