import pytest
from django.conf import settings
from django.contrib.messages.storage.base import Message
from django.contrib.messages.storage.cookie import MessageEncoder, MessageDecoder


def test_issue_reproduction():
    """Test that empty string extra_tags are preserved during serialization/deserialization."""
    # Configure Django settings if not already configured
    if not settings.configured:
        settings.configure()
    
    # Create a message with empty string extra_tags
    original_message = Message(10, "Here is a message", extra_tags="")
    
    # Encode and then decode the message
    encoded_message = MessageEncoder().encode(original_message)
    decoded_message = MessageDecoder().decode(encoded_message)
    
    # The bug: empty string gets converted to None
    assert original_message.extra_tags == ""
    assert decoded_message.extra_tags == "", f"Expected empty string, got {decoded_message.extra_tags!r}"