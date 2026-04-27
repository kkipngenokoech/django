import os
import tempfile
from django.db import models
from django.db.migrations.writer import MigrationWriter
from django.db.migrations.operations import CreateModel
from django.db.migrations import Migration
from django.test import TestCase


def get_dynamic_path():
    return '/dynamic/path'


class TestModel(models.Model):
    file = models.FilePathField(path=get_dynamic_path)
    
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    """Test that FilePathField path parameter accepts callables and preserves them in migrations."""
    # Create a migration with a model that has FilePathField with callable path
    operation = CreateModel(
        name='TestModel',
        fields=[
            ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('file', models.FilePathField(path=get_dynamic_path)),
        ],
    )
    
    migration = Migration('0001_initial', 'test_app')
    migration.operations = [operation]
    
    # Generate migration content
    writer = MigrationWriter(migration, include_header=False)
    migration_content = writer.as_string()
    
    # The bug: callable should be preserved in migration, but currently it gets evaluated
    # This test will fail because the current implementation evaluates the callable immediately
    # and puts the result ('/dynamic/path') in the migration instead of preserving the callable reference
    assert 'get_dynamic_path' in migration_content, f"Callable path function should be preserved in migration, but got: {migration_content}"