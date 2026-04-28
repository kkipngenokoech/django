import pytest
from django.core import checks
from django.db import models
from django.test import TestCase, override_settings
from django.apps import apps
from django.conf import settings


def test_issue_reproduction():
    """Test that models.W042 is incorrectly raised on inherited manually specified primary key."""
    
    # Create a parent model with an explicit primary key
    class ParentModel(models.Model):
        id = models.AutoField(primary_key=True)
        name = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'test_app'
    
    # Create a child model that should inherit the primary key
    class ChildModel(ParentModel):
        description = models.CharField(max_length=200)
        
        class Meta:
            app_label = 'test_app'
    
    # Run the system checks on the child model
    errors = checks.run_checks(app_configs=None, tags=None, include_deployment_checks=False)
    
    # Filter for W042 warnings on our child model
    w042_errors = [
        error for error in errors 
        if error.id == 'models.W042' and 'ChildModel' in str(error.obj)
    ]
    
    # The bug: W042 should NOT be raised for ChildModel since it inherits 
    # a primary key from ParentModel, but currently it is raised incorrectly
    assert len(w042_errors) > 0, "Expected W042 to be incorrectly raised (demonstrating the bug)"
    
    # Verify the parent model doesn't have the warning (it has explicit PK)
    parent_w042_errors = [
        error for error in errors 
        if error.id == 'models.W042' and 'ParentModel' in str(error.obj)
    ]
    
    # Parent should not have W042 since it has explicit primary key
    assert len(parent_w042_errors) == 0, "Parent model should not have W042 warning"