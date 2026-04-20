from django import forms
import pytest
from django.core.exceptions import ValidationError

def test_issue_reproduction():
    """Test that URLField.clean raises ValidationError, not ValueError for malformed IPv6 URLs."""
    url_field = forms.URLField()
    
    # This should raise ValidationError, not ValueError
    with pytest.raises(ValueError, match="Invalid IPv6 URL"):
        url_field.clean('////]@N.AN')