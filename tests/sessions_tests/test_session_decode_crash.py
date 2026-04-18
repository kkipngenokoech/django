import pytest
from django.contrib.sessions.backends.base import SessionBase
from django.core.signing import BadSignature


class TestSessionStore(SessionBase):
    """Minimal implementation of SessionBase for testing."""
    
    def __init__(self, session_key=None):
        super().__init__(session_key)
        self._storage = {}
    
    def exists(self, session_key):
        return session_key in self._storage
    
    def create(self):
        self._session_key = self._get_new_session_key()
        self._storage[self._session_key] = {}
    
    def save(self, must_create=False):
        if must_create and self.session_key in self._storage:
            raise Exception("Session already exists")
        self._storage[self.session_key] = self._session
    
    def delete(self, session_key=None):
        key = session_key or self.session_key
        if key in self._storage:
            del self._storage[key]
    
    def load(self):
        # Simulate loading corrupted session data that will cause BadSignature
        corrupted_data = "corrupted.session.data.with.invalid.signature"
        return self.decode(corrupted_data)


def test_issue_reproduction():
    """Test that decoding invalid session data crashes instead of returning empty session."""
    session = TestSessionStore()
    
    # This should crash with BadSignature on current code
    # but should return empty dict after fix
    with pytest.raises(BadSignature):
        session._get_session()