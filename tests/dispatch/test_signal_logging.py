import logging
from django.dispatch import Signal


def test_issue_reproduction():
    """Test that Signal.send_robust() logs exceptions from receivers."""
    # Create a signal
    test_signal = Signal()
    
    # Create a receiver that raises an exception
    def failing_receiver(sender, **kwargs):
        raise ValueError("Test exception from receiver")
    
    # Connect the failing receiver
    test_signal.connect(failing_receiver)
    
    # Set up logging capture
    with logging.getLogger('django.dispatch.dispatcher').propagate:
        with logging.getLogger().handlers[0] if logging.getLogger().handlers else None:
            # This is a simplified approach - in reality we'd need proper log capture
            # But the key point is that currently NO logging happens
            pass
    
    # Send signal robustly - this should log the exception but currently doesn't
    responses = test_signal.send_robust(sender=None)
    
    # Verify the exception was returned (this works)
    assert len(responses) == 1
    receiver, response = responses[0]
    assert isinstance(response, ValueError)
    assert str(response) == "Test exception from receiver"
    
    # The issue is that no logging occurs - we need to verify logging happened
    # This test will fail because the current implementation doesn't log exceptions
    # We'll use a more direct approach by checking if logger.exception was called
    
    import unittest.mock
    with unittest.mock.patch('logging.getLogger') as mock_get_logger:
        mock_logger = unittest.mock.Mock()
        mock_get_logger.return_value = mock_logger
        
        # Send signal again with mocked logger
        test_signal.send_robust(sender=None)
        
        # This assertion will fail because send_robust doesn't call logger.exception
        mock_logger.exception.assert_called_once()