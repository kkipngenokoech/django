import pytest
from django.db import models
from django.test import TestCase
from django.test.utils import override_settings


class SimpleModel(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_app'


@override_settings(DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
})
def test_issue_reproduction():
    # Create the table
    from django.db import connection
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(SimpleModel)
    
    # Create and save an instance
    instance = SimpleModel(name='test')
    instance.save()
    
    # Verify it has a PK
    assert instance.pk is not None
    original_pk = instance.pk
    
    # Delete the instance
    instance.delete()
    
    # The PK should be None after deletion (this is the bug - it currently isn't None)
    assert instance.pk is None, f"Expected PK to be None after delete(), but got {instance.pk}"