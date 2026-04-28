import pytest
from django.core import checks
from django.db import models
from django.test import TestCase, override_settings


def test_issue_reproduction():
    """Test that W042 warning is incorrectly raised on inherited primary keys."""
    
    # Create a parent model with an explicit primary key
    class ParentModel(models.Model):
        id = models.AutoField(primary_key=True)
        name = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'test_app'
    
    # Create a child model that should inherit the primary key
    class ChildModel(ParentModel):
        description = models.TextField()
        
        class Meta:
            app_label = 'test_app'
    
    # Run the model checks
    errors = checks.run_checks(app_configs=None, tags=None, include_deployment_checks=False)
    
    # Filter for W042 warnings on our child model
    w042_warnings = [
        error for error in errors 
        if error.id == 'models.W042' and 'ChildModel' in str(error.obj)
    ]
    
    # The bug is that W042 is raised even though ChildModel inherits a primary key
    # This assertion will FAIL on the buggy code because w042_warnings will not be empty
    assert len(w042_warnings) == 0, f"W042 warning incorrectly raised on inherited primary key: {w042_warnings}"