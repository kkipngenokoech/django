from django.db import models
from django.db.models.fields.related import *
from django.db.models.fields.files import *
from django.db.models.fields.json import *


class AutoFieldMeta(type):
    """
    Metaclass to maintain backward inheritance compatibility for AutoField.
    """
    
    @property
    def _subclasses(self):
        return (
            models.AutoField, models.BigAutoField, models.SmallAutoField
        )
    
    def __instancecheck__(cls, instance):
        return any(
            isinstance(instance, subclass)
            for subclass in cls._subclasses
        )
    
    def __subclasscheck__(cls, subclass):
        return any(
            issubclass(subclass, parent)
            for parent in cls._subclasses
        )


class AutoField(models.Field, metaclass=AutoFieldMeta):
    """
    An IntegerField which automatically populates from an auto-incrementing
    counter.
    """
    pass


class BigAutoField(models.BigIntegerField):
    """
    A 64-bit integer, much like an AutoField except that it is
    guaranteed to fit numbers from 1 to 9223372036854775807.
    """
    pass


class SmallAutoField(models.SmallIntegerField):
    """
    Like an AutoField, but only allows values under a certain
    (database-dependent) limit.
    """
    pass
