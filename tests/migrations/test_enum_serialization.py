import enum
from django.utils.translation import gettext_lazy as _
from django.db.migrations.serializer import serializer_factory

def test_issue_reproduction():
    class Status(enum.Enum):
        GOOD = _('Good')
        BAD = _('Bad')
    
    # Serialize the enum value
    serializer = serializer_factory(Status.GOOD)
    serialized_string, imports = serializer.serialize()
    
    # The bug: serialized string should use enum name, not value
    # Current buggy behavior creates: Status(<translated_value>)
    # Expected behavior should create: Status.GOOD
    assert 'Status.GOOD' in serialized_string, f"Expected enum name in serialization, got: {serialized_string}"