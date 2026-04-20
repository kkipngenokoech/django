import pytest
from django.db.models.enums import TextChoices
from django.db.models.fields.choices import CharField

class MyChoice(TextChoices):
    FIRST_CHOICE = "first", "The first choice, it is"
    SECOND_CHOICE = "second", "The second choice, it is"

class MyObject:
    """Mock model with CharField using TextChoices"""
    def __init__(self):
        self.my_str_value = CharField(max_length=10, choices=MyChoice.choices)
    
    @classmethod
    def objects_create(cls, **kwargs):
        obj = cls()
        for key, value in kwargs.items():
            setattr(obj, key, value)
        return obj

def test_issue_reproduction():
    """Test that demonstrates TextChoices field returns str instead of enum"""
    # Create object with TextChoices enum value
    my_object = MyObject.objects_create(my_str_value=MyChoice.FIRST_CHOICE)
    
    # This should pass - the field value should be a string
    assert isinstance(my_object.my_str_value, str), f"Expected str, got {type(my_object.my_str_value)}"
    assert str(my_object.my_str_value) == "first"
    
    # Verify the fix works - my_str_value should be a string, not an enum instance
    assert my_object.my_str_value == "first"
    assert not isinstance(my_object.my_str_value, MyChoice)
