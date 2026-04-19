import pytest
from django.db import models
from django.test import TestCase
from django.utils.translation import gettext_lazy as _


class MyChoice(models.TextChoices):
    FIRST_CHOICE = "first", _("The first choice, it is")
    SECOND_CHOICE = "second", _("The second choice, it is")


class MyIntChoice(models.IntegerChoices):
    FIRST_CHOICE = 1, _("The first choice, it is")
    SECOND_CHOICE = 2, _("The second choice, it is")


class MyObject(models.Model):
    my_str_value = models.CharField(max_length=10, choices=MyChoice.choices)
    my_int_value = models.IntegerField(choices=MyIntChoice.choices)
    
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    """Test that TextChoices and IntegerChoices field values return primitive types."""
    # Create object with TextChoices
    my_object = MyObject(my_str_value=MyChoice.FIRST_CHOICE, my_int_value=MyIntChoice.FIRST_CHOICE)
    
    # Test TextChoices field returns str, not enum
    assert isinstance(my_object.my_str_value, str), f"Expected str, got {type(my_object.my_str_value)}"
    assert my_object.my_str_value == "first"
    
    # Test IntegerChoices field returns int, not enum
    assert isinstance(my_object.my_int_value, int), f"Expected int, got {type(my_object.my_int_value)}"
    assert my_object.my_int_value == 1