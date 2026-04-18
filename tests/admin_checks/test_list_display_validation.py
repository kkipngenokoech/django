import pytest
from django.contrib import admin
from django.core import checks
from django.db import models
from django.test import TestCase


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    
    class Meta:
        app_label = 'test_app'


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    
    class Meta:
        app_label = 'test_app'


class QuestionAdmin(admin.ModelAdmin):
    list_display = ['choice']  # Invalid field - should trigger E108


def test_issue_reproduction():
    """Test that E108 error check catches invalid field names in list_display."""
    # Register the admin with invalid list_display
    admin_obj = QuestionAdmin(Question, admin.site)
    
    # Run the admin checks - this should catch the invalid 'choice' field
    errors = admin_obj.check()
    
    # Should find an E108 error for the invalid 'choice' field in list_display
    e108_errors = [error for error in errors if error.id == 'admin.E108']
    
    # This assertion will FAIL because the current code doesn't catch this case
    assert len(e108_errors) > 0, "Expected E108 error for invalid field 'choice' in list_display, but none found"