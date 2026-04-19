import pytest
from django.contrib.sessions.backends.base import SessionBase
from django.core.signing import BadSignature


def test_issue_reproduction():
    """Test that decoding invalid session data should not crash but return empty dict."""
    session = SessionBase()
    
    # Create invalid session data that will cause BadSignature when decoded
    invalid_session_data = "invalid.session.data.that.will.cause.badsignature"
    
    # This should not raise an exception but return an empty dict
    # Currently this will raise BadSignature and crash
    result = session.decode(invalid_session_data)
    
    # Should return empty dict for invalid session data
    assert result == {}