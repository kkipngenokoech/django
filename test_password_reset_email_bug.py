from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.test import TestCase


def test_issue_reproduction():
    """Test that password reset tokens should be invalidated when user email changes."""
    # Create a user with an email
    user = User.objects.create_user('testuser', 'original@example.com', 'testpass')
    
    # Generate a password reset token
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    
    # Verify the token is valid with original email
    assert token_generator.check_token(user, token) is True
    
    # Change the user's email address
    user.email = 'changed@example.com'
    user.save()
    
    # The token should now be invalid since email changed, but currently it's still valid (bug)
    # This assertion will FAIL on current code, demonstrating the bug
    assert token_generator.check_token(user, token) is False