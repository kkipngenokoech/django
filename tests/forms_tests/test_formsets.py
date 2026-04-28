import pytest
from django.forms import modelformset_factory, Form, CharField
from django.db import models
from django.test import TestCase
from django.forms.formsets import formset_factory


class TestModel(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test'


class SimpleForm(Form):
    name = CharField()


class FormsetEmptyPermittedTests(TestCase):
    """Test that empty_permitted in form_kwargs doesn't break empty_form access."""
    
    def test_empty_form_with_empty_permitted_true(self):
        """Test that accessing empty_form works when empty_permitted=True is in form_kwargs."""
        FormSet = formset_factory(SimpleForm)
        
        # This should not raise a KeyError when accessing empty_form
        formset = FormSet(
            form_kwargs={'empty_permitted': True}
        )
        
        # Accessing empty_form should work without raising KeyError
        empty_form = formset.empty_form
        self.assertIsNotNone(empty_form)
        # empty_form should always have empty_permitted=True regardless of form_kwargs
        self.assertTrue(empty_form.empty_permitted)
    
    def test_empty_form_with_empty_permitted_false(self):
        """Test that accessing empty_form works when empty_permitted=False is in form_kwargs."""
        FormSet = formset_factory(SimpleForm)
        
        # This should not raise a KeyError when accessing empty_form
        formset = FormSet(
            form_kwargs={'empty_permitted': False}
        )
        
        # Accessing empty_form should work without raising KeyError
        empty_form = formset.empty_form
        self.assertIsNotNone(empty_form)
        # empty_form should always have empty_permitted=True regardless of form_kwargs
        self.assertTrue(empty_form.empty_permitted)
    
    def test_modelformset_empty_form_with_empty_permitted_true(self):
        """Test that accessing empty_form works with modelformset when empty_permitted=True."""
        FormSet = modelformset_factory(TestModel, fields=['name'])
        
        # This should not raise a KeyError when accessing empty_form
        formset = FormSet(
            queryset=TestModel.objects.none(),
            form_kwargs={'empty_permitted': True}
        )
        
        # Accessing empty_form should work without raising KeyError
        empty_form = formset.empty_form
        self.assertIsNotNone(empty_form)
        # empty_form should always have empty_permitted=True regardless of form_kwargs
        self.assertTrue(empty_form.empty_permitted)
    
    def test_modelformset_empty_form_with_empty_permitted_false(self):
        """Test that accessing empty_form works with modelformset when empty_permitted=False."""
        FormSet = modelformset_factory(TestModel, fields=['name'])
        
        # This should not raise a KeyError when accessing empty_form
        formset = FormSet(
            queryset=TestModel.objects.none(),
            form_kwargs={'empty_permitted': False}
        )
        
        # Accessing empty_form should work without raising KeyError
        empty_form = formset.empty_form
        self.assertIsNotNone(empty_form)
        # empty_form should always have empty_permitted=True regardless of form_kwargs
        self.assertTrue(empty_form.empty_permitted)


def test_issue_reproduction():
    """Test that accessing empty_form works when empty_permitted is in form_kwargs."""
    # Create a modelformset with empty_permitted in form_kwargs
    FormSet = modelformset_factory(TestModel, fields=['name'])
    
    # This should not raise a KeyError when accessing empty_form
    formset = FormSet(
        queryset=TestModel.objects.none(),
        form_kwargs={'empty_permitted': True}
    )
    
    # Accessing empty_form should work without raising KeyError
    # This will fail on the current buggy code
    empty_form = formset.empty_form
    assert empty_form is not None
