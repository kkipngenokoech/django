import pytest
from django.forms import URLField
from django.core.exceptions import ValidationError

def test_issue_reproduction():
    """Test that URLField.clean() raises ValidationError, not ValueError for malformed URLs."""
    field = URLField()
    
    # This should raise ValidationError, but currently raises ValueError
    with pytest.raises(ValueError, match="Invalid IPv6 URL"):
        field.clean('////]@N.AN')