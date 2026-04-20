import enum
from django.db.migrations.serializer import EnumSerializer
from django.utils.translation import gettext_lazy as _

def test_issue_reproduction():
    """Test that enum serialization uses name instead of value for translatable enums."""
    
    class Status(enum.Enum):
        GOOD = _('Good')
        BAD = _('Bad')
        
        def __str__(self):
            return self.name
    
    # Serialize the enum
    serializer = EnumSerializer(Status.GOOD)
    serialized_string, imports = serializer.serialize()
    
    # The current implementation incorrectly uses the value
    # This will fail because it should use Status.GOOD instead of Status('Good')
    expected = "test_issue_reproduction.<locals>.Status.GOOD"
    assert expected in serialized_string, f"Expected enum name serialization, got: {serialized_string}"