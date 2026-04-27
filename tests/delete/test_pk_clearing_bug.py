import pytest
from django.db import models, connection
from django.test import TestCase, TransactionTestCase
from django.test.utils import isolate_apps


@isolate_apps('test_delete_pk_clearing')
class TestDeletePKClearing(TransactionTestCase):
    """
    Test that delete() clears primary keys on model instances.
    """
    
    def setUp(self):
        # Create a simple model with no dependencies for fast delete
        class SimpleModel(models.Model):
            name = models.CharField(max_length=100)
            
            class Meta:
                app_label = 'test_delete_pk_clearing'
        
        self.SimpleModel = SimpleModel
        
        # Create the table
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(SimpleModel)
    
    def tearDown(self):
        # Drop the table
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(self.SimpleModel)
    
    def test_issue_reproduction(self):
        """
        Test that delete() on instances of models without dependencies clears PKs.
        
        This test reproduces the bug where fast delete path doesn't clear the
        primary key on the model instance after deletion.
        """
        # Create an instance
        instance = self.SimpleModel.objects.create(name='test')
        original_pk = instance.pk
        
        # Verify the instance has a PK before deletion
        assert instance.pk is not None
        assert instance.pk == original_pk
        
        # Delete the instance - this should trigger fast delete path
        # since SimpleModel has no dependencies
        deleted_count, deleted_dict = instance.delete()
        
        # Verify deletion occurred
        assert deleted_count == 1
        assert deleted_dict == {'test_delete_pk_clearing.SimpleModel': 1}
        
        # The bug: PK should be None after deletion but it's not cleared in fast delete
        assert instance.pk is None, f"Expected pk to be None after deletion, but got {instance.pk}"
