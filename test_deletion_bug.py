#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings
from django.db import models

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
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            '__main__',
        ],
        USE_TZ=False,
    )

django.setup()

from django.db import connection

class SimpleModel(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = '__main__'

# Create the table
with connection.schema_editor() as schema_editor:
    schema_editor.create_model(SimpleModel)

def test_deletion_bug():
    # Create and save a model instance with no dependencies
    instance = SimpleModel(name='test')
    instance.save()
    
    # Verify it has a primary key
    original_pk = instance.pk
    print(f"Original PK: {original_pk}")
    assert original_pk is not None
    
    # Delete the instance
    result = instance.delete()
    print(f"Delete result: {result}")
    
    # The primary key should be set to None after deletion
    print(f"PK after deletion: {instance.pk}")
    
    if instance.pk is None:
        print("✓ PASS: PK was correctly cleared after deletion")
        return True
    else:
        print("✗ FAIL: PK was not cleared after deletion")
        return False

if __name__ == '__main__':
    success = test_deletion_bug()
    sys.exit(0 if success else 1)