import logging
from django.dispatch import Signal


def test_issue_reproduction():
    """Test that send_robust logs exceptions from receivers."""
    # Create a signal
    test_signal = Signal()
    
    # Create a receiver that raises an exception
    def failing_receiver(sender, **kwargs):
        raise ValueError("Test exception from receiver")
    
    # Connect the failing receiver
    test_signal.connect(failing_receiver)
    
    # Set up logging capture
    with logging.disable(logging.NOTSET):
        logger = logging.getLogger('django.dispatch.dispatcher')
        
        # Create a list to capture log records
        log_records = []
        
        class TestHandler(logging.Handler):
            def emit(self, record):
                log_records.append(record)
        
        handler = TestHandler()
        handler.setLevel(logging.ERROR)
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)
        
        try:
            # Send signal using send_robust - should log the exception
            responses = test_signal.send_robust(sender=None)
            
            # Verify the exception was caught and returned
            assert len(responses) == 1
            receiver, response = responses[0]
            assert isinstance(response, ValueError)
            assert str(response) == "Test exception from receiver"
            
            # This assertion will fail on current code since no logging occurs
            assert len(log_records) > 0, "Expected exception to be logged but no log records found"
            
            # Verify the log record contains exception information
            log_record = log_records[0]
            assert log_record.levelno == logging.ERROR
            assert "Test exception from receiver" in log_record.getMessage() or log_record.exc_info is not None
            
        finally:
            logger.removeHandler(handler)