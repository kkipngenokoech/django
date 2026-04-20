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
    
    # Serialize the message
    encoded_message = MessageEncoder().encode(original_message)
    
    # Deserialize the message
    decoded_message = MessageDecoder().decode(encoded_message)
    
    # The bug: empty string extra_tags becomes None after serialization/deserialization
    assert original_message.extra_tags == ""
    assert decoded_message.extra_tags == "", f"Expected empty string, got {decoded_message.extra_tags!r}"