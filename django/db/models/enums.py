from enum import Enum

class TextChoices(Enum):
    """Django-style TextChoices that behave like enum choices"""
    def __new__(cls, value, label):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.label = label
        return obj
    
    @classmethod
    @property
    def choices(cls):
        return [(choice.value, choice.label) for choice in cls]

class IntegerChoices(Enum):
    """Django-style IntegerChoices that behave like enum choices"""
    def __new__(cls, value, label):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.label = label
        return obj
    
    @classmethod
    @property
    def choices(cls):
        return [(choice.value, choice.label) for choice in cls]

def is_choice_enum(value):
    """Check if a value is a choice enum instance"""
    return isinstance(value, (TextChoices, IntegerChoices))

def get_choice_value(value):
    """Extract primitive value from choice enum"""
    if is_choice_enum(value):
        return value.value
    return value
