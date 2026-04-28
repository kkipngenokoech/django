import pytest
from django.contrib.sessions.backends.base import SessionBase
from django.core.signing import BadSignature
from django.conf import settings
from django.test import override_settings


class TestSessionBackend(SessionBase):
    """Minimal session backend for testing decode behavior."""
    
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
        # This simulates loading corrupted session data that will cause BadSignature
        corrupted_data = "corrupted:session:data:with:invalid:signature"
        return self.decode(corrupted_data)


@override_settings(
    SECRET_KEY='test-secret-key',
    SESSION_SERIALIZER='django.contrib.sessions.serializers.JSONSerializer'
)
def test_issue_reproduction():
    """Test that decoding invalid session data crashes with BadSignature."""
    session = TestSessionBackend()
    session._session_key = 'test_key'
    
    # This should crash when trying to access the session data
    # because load() will call decode() with corrupted data
    with pytest.raises((BadSignature, AttributeError)):
        _ = session._session  # This triggers load() which calls decode()