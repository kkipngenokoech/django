import django
from django.db import models
from django.test import TestCase

def test_issue_reproduction():
    class A(models.Model):
        foo_choice = [("A", "output1"), ("B", "output2")]
        field_foo = models.CharField(max_length=254, choices=foo_choice)
        
        class Meta:
            abstract = True
    
    class B(A):
        foo_choice = [("A", "output1"), ("B", "output2"), ("C", "output3")]
        field_foo = models.CharField(max_length=254, choices=foo_choice)
    
    # Create an instance with the new choice value
    instance = B(field_foo="C")
    
    # This should return "output3" but currently returns "C"
    display_value = instance.get_field_foo_display()
    assert display_value == "output3", f"Expected 'output3' but got '{display_value}'"