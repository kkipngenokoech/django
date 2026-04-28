import enum
from django.utils.translation import gettext_lazy as _
from django.db.migrations.serializer import serializer_factory

def test_issue_reproduction():
    """Test that enum serialization uses value instead of name, causing translation issues."""
    
    class Status(enum.Enum):
        GOOD = _('Good')
        BAD = _('Bad')
        
        def __str__(self):
            return self.name
    
    # Serialize the enum value
    serializer = serializer_factory(Status.GOOD)
    serialized_string, imports = serializer.serialize()
    
    # The current implementation should serialize as Status.GOOD(<translated_value>)
    # which will fail when the translation changes
    # We expect it to contain the translated value 'Good' rather than the stable name 'GOOD'
    assert 'Good' in serialized_string, f"Expected 'Good' in serialized string, got: {serialized_string}"
    assert 'GOOD' not in serialized_string, f"Should not contain enum name 'GOOD', got: {serialized_string}"
    
    # Verify the serialized form uses the enum constructor with the value
    expected_pattern = "Status('Good')"
    assert expected_pattern in serialized_string or "Status(" in serialized_string, f"Expected enum constructor pattern, got: {serialized_string}"
    
    # The issue is that this serialization will break when translations change
    # because it uses the translated value instead of the stable enum name