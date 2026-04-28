import pytest
from django.forms import URLField
from django.core.exceptions import ValidationError

def test_issue_reproduction():
    """Test that URLField.clean() raises ValidationError instead of ValueError for malformed URLs."""
    field = URLField()
    
    # This should raise ValidationError, not ValueError
    with pytest.raises(ValidationError):
        field.clean('////]@N.AN')