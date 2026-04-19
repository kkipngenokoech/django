from django.core.checks import Error
from django.db import models


class ModelBase(type):
    """Metaclass for all models."""
    
    def __new__(cls, name, bases, namespace, **kwargs):
        super_new = super().__new__
        
        # Create the class
        new_class = super_new(cls, name, bases, namespace)
        
        # Add model checking
        if hasattr(new_class, '_meta'):
            new_class.check = classmethod(_check_model)
        
        return new_class


def _check_model(cls, **kwargs):
    """Check model for various issues."""
    errors = []
    errors.extend(_check_unique_constraints(cls))
    errors.extend(_check_unique_together(cls))
    return errors


def _check_unique_together(model):
    """Check unique_together option."""
    errors = []
    if hasattr(model._meta, 'unique_together'):
        unique_together = model._meta.unique_together
        
        for fields in unique_together:
            for field_name in fields:
                try:
                    model._meta.get_field(field_name)
                except models.FieldDoesNotExist:
                    errors.append(
                        Error(
                            "'unique_together' refers to the nonexistent field '%s'." % field_name,
                            obj=model,
                            id='models.E012',
                        )
                    )
    
    return errors


def _check_unique_constraints(model):
    """Check UniqueConstraint fields exist."""
    errors = []
    
    if hasattr(model._meta, 'constraints'):
        for constraint in model._meta.constraints:
            if isinstance(constraint, models.UniqueConstraint):
                for field_name in constraint.fields:
                    try:
                        model._meta.get_field(field_name)
                    except models.FieldDoesNotExist:
                        errors.append(
                            Error(
                                "'UniqueConstraint' refers to the nonexistent field '%s'." % field_name,
                                obj=model,
                                id='models.E012',
                            )
                        )
    
    return errors


class Model(metaclass=ModelBase):
    """Base class for all models."""
    pass
