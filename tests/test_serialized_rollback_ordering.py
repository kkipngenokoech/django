import pytest
from django.db import models, connection
from django.test import TransactionTestCase
from django.apps import apps
from django.db.backends.base.creation import BaseDatabaseCreation
from io import StringIO
from django.core import serializers


class Author(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_app'


class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    """Test that deserialize_db_from_string fails due to foreign key ordering constraints."""
    
    # Create test models in the database
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Author)
        schema_editor.create_model(Book)
    
    try:
        # Create some test data with foreign key relationships
        author = Author.objects.create(name="Test Author")
        book = Book.objects.create(title="Test Book", author=author)
        
        # Serialize the data using the same method as TransactionTestCase
        creation = BaseDatabaseCreation(connection)
        
        # Build app list similar to serialize_db_to_string
        app_list = [(type('MockAppConfig', (), {
            'models_module': True,
            'label': 'test_app',
            'name': 'test_app'
        })(), None)]
        
        # Create serialized data that will have ordering issues
        # We'll manually create JSON that has Book before Author to trigger the issue
        serialized_data = [
            {
                "model": "test_app.book",
                "pk": book.pk,
                "fields": {
                    "title": "Test Book",
                    "author": author.pk
                }
            },
            {
                "model": "test_app.author", 
                "pk": author.pk,
                "fields": {
                    "name": "Test Author"
                }
            }
        ]
        
        import json
        bad_order_json = json.dumps(serialized_data)
        
        # Clear the database
        Book.objects.all().delete()
        Author.objects.all().delete()
        
        # This should fail because Book references Author but Author comes after Book in the JSON
        # The current implementation doesn't wrap in a transaction, so foreign key constraint fails
        with pytest.raises(Exception) as exc_info:
            creation.deserialize_db_from_string(bad_order_json)
        
        # The exception should be related to foreign key constraint or integrity error
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in [
            'foreign key', 'constraint', 'integrity', 'does not exist', 'violates'
        ]), f"Expected foreign key constraint error, got: {exc_info.value}"
        
    finally:
        # Clean up the test models
        with connection.schema_editor() as schema_editor:
            try:
                schema_editor.delete_model(Book)
            except:
                pass
            try:
                schema_editor.delete_model(Author)
            except:
                pass