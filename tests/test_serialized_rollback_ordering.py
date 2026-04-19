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
    # Create test models in memory
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Author)
        schema_editor.create_model(Book)
    
    try:
        # Create test data with foreign key relationship
        author = Author.objects.create(name='Test Author')
        book = Book.objects.create(title='Test Book', author=author)
        
        # Serialize the data (this works fine)
        creation = BaseDatabaseCreation(connection)
        serialized_data = creation.serialize_db_to_string()
        
        # Clear the database
        Book.objects.all().delete()
        Author.objects.all().delete()
        
        # Manually create problematic serialized data where Book comes before Author
        # This simulates the ordering issue described in the bug report
        problematic_data = [
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
        problematic_json = json.dumps(problematic_data)
        
        # This should fail due to foreign key constraint violation
        # because Book references Author but Author hasn't been saved yet
        creation.deserialize_db_from_string(problematic_json)
        
        # If we get here without an exception, the bug is fixed
        assert Book.objects.count() == 1
        assert Author.objects.count() == 1
        
    finally:
        # Clean up test models
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(Book)
            schema_editor.delete_model(Author)