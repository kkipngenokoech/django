#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        USE_TZ=True,
    )

django.setup()

from django.forms import DurationField
from django.core.exceptions import ValidationError

def test_current_behavior():
    """Test current DurationField error message format."""
    field = DurationField()
    
    try:
        field.clean('invalid_duration')
    except ValidationError as e:
        print("Current error message:", str(e))
        print("Error message args:", e.args)
        return str(e)
    
    return None

if __name__ == "__main__":
    result = test_current_behavior()
    print("Result:", result)