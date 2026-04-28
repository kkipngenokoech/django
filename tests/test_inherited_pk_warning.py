import pytest
from django.core import checks
from django.db import models
from django.test import TestCase
from django.apps import apps
from django.conf import settings


def test_issue_reproduction():
    """Test that inherited models with manually specified primary keys don't trigger W042."""
    
    # Create a parent model with an explicitly defined primary key
    class ParentModel(models.Model):
        id = models.BigAutoField(primary_key=True)
        name = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'test_app'
    
    # Create a child model that inherits the primary key
    class ChildModel(ParentModel):
        description = models.TextField()
        
        class Meta:
            app_label = 'test_app'
    
    # Run the model checks on the child model
    errors = ChildModel.check()
    
    # Filter for W042 warnings specifically
    w042_warnings = [error for error in errors if error.id == 'models.W042']
    
    # The child model should NOT have W042 warnings since it inherits
    # a manually specified primary key from the parent
    assert len(w042_warnings) == 0, f"Child model incorrectly flagged with W042: {w042_warnings}"