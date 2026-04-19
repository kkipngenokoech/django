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
        author = Author.objects.create(name="Test Author")
        book = Book.objects.create(title="Test Book", author=author)
        
        # Serialize the data (this works fine)
        creation = BaseDatabaseCreation(connection)
        serialized_data = creation.serialize_db_to_string()
        
        # Clear the database
        Book.objects.all().delete()
        Author.objects.all().delete()
        
        # Create a malformed serialized string where Book comes before Author
        # This simulates the ordering issue described in the bug report
        data = StringIO(serialized_data)
        objects = list(serializers.deserialize("json", data, using=connection.alias))
        
        # Manually reorder to put Book before Author (this causes the constraint violation)
        book_obj = None
        author_obj = None
        for obj in objects:
            if obj.object.__class__.__name__ == 'Book':
                book_obj = obj
            elif obj.object.__class__.__name__ == 'Author':
                author_obj = obj
        
        if book_obj and author_obj:
            # Create malformed JSON with Book before Author
            malformed_objects = [book_obj, author_obj]
            out = StringIO()
            serializers.serialize("json", [obj.object for obj in malformed_objects], indent=None, stream=out)
            malformed_data = out.getvalue()
            
            # This should fail due to foreign key constraint violation
            # because Book references Author but Author hasn't been saved yet
            creation.deserialize_db_from_string(malformed_data)
            
    finally:
        # Clean up test models
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(Book)
            schema_editor.delete_model(Author)