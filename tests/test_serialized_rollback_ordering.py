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
        # Create test data
        author = Author.objects.create(name="Test Author")
        book = Book.objects.create(title="Test Book", author=author)
        
        # Serialize the data
        creation = BaseDatabaseCreation(connection)
        serialized_data = creation.serialize_db_to_string()
        
        # Clear the database
        Book.objects.all().delete()
        Author.objects.all().delete()
        
        # Manually craft serialized data where Book comes before Author
        # to simulate the ordering issue
        data = [
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
        bad_serialized_data = json.dumps(data)
        
        # This should fail due to foreign key constraint
        # Book references Author but Author comes after Book in the data
        with pytest.raises(Exception):  # Could be IntegrityError or similar
            creation.deserialize_db_from_string(bad_serialized_data)
            
    finally:
        # Clean up test models
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(Book)
            schema_editor.delete_model(Author)