import logging
from unittest.mock import patch
from django.dispatch import Signal


def test_issue_reproduction():
    """Test that Signal.send_robust() logs exceptions from receivers."""
    signal = Signal()
    
    def failing_receiver(sender, **kwargs):
        raise ValueError("Test exception from receiver")
    
    signal.connect(failing_receiver)
    
    # Mock the logger to capture log calls
    with patch('django.dispatch.dispatcher.logger') as mock_logger:
        # Send signal which should trigger exception in receiver
        responses = signal.send_robust(sender=None)
        
        # Verify the exception was returned in responses
        assert len(responses) == 1
        receiver, response = responses[0]
        assert isinstance(response, ValueError)
        assert str(response) == "Test exception from receiver"
        
        # This should fail on current code - no logging happens
        mock_logger.exception.assert_called_once()