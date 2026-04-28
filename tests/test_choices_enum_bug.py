import pytest
from django.db import models
from django.test import TestCase
from django.utils.translation import gettext_lazy as _


class MyTextChoice(models.TextChoices):
    FIRST_CHOICE = "first", _("The first choice, it is")
    SECOND_CHOICE = "second", _("The second choice, it is")


class MyIntChoice(models.IntegerChoices):
    FIRST_CHOICE = 1, _("The first choice, it is")
    SECOND_CHOICE = 2, _("The second choice, it is")


class MyTextObject(models.Model):
    my_str_value = models.CharField(max_length=10, choices=MyTextChoice.choices)
    
    class Meta:
        app_label = 'test_app'


class MyIntObject(models.Model):
    my_int_value = models.IntegerField(choices=MyIntChoice.choices)
    
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    """Test that TextChoices and IntegerChoices fields return primitive types, not enum instances."""
    
    # Test TextChoices with CharField
    text_obj = MyTextObject(my_str_value=MyTextChoice.FIRST_CHOICE)
    
    # The field value should be a string, not an enum instance
    assert isinstance(text_obj.my_str_value, str), f"Expected str, got {type(text_obj.my_str_value)}"
    assert text_obj.my_str_value == "first", f"Expected 'first', got {text_obj.my_str_value!r}"
    
    # Test after save/reload cycle (simulating database retrieval)
    text_obj.save()
    reloaded_text_obj = MyTextObject.objects.get(pk=text_obj.pk)
    
    # This is where the bug manifests - the reloaded object returns enum instance instead of string
    assert isinstance(reloaded_text_obj.my_str_value, str), f"Expected str after reload, got {type(reloaded_text_obj.my_str_value)}"
    assert reloaded_text_obj.my_str_value == "first", f"Expected 'first' after reload, got {reloaded_text_obj.my_str_value!r}"
    
    # Test IntegerChoices with IntegerField
    int_obj = MyIntObject(my_int_value=MyIntChoice.FIRST_CHOICE)
    
    # The field value should be an int, not an enum instance
    assert isinstance(int_obj.my_int_value, int), f"Expected int, got {type(int_obj.my_int_value)}"
    assert int_obj.my_int_value == 1, f"Expected 1, got {int_obj.my_int_value!r}"
    
    # Test after save/reload cycle
    int_obj.save()
    reloaded_int_obj = MyIntObject.objects.get(pk=int_obj.pk)
    
    # This is where the bug manifests for IntegerChoices too
    assert isinstance(reloaded_int_obj.my_int_value, int), f"Expected int after reload, got {type(reloaded_int_obj.my_int_value)}"
    assert reloaded_int_obj.my_int_value == 1, f"Expected 1 after reload, got {reloaded_int_obj.my_int_value!r}"
    
    # Test that string conversion works correctly
    assert str(reloaded_text_obj.my_str_value) == "first"
    assert str(reloaded_int_obj.my_int_value) == "1"