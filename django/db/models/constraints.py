from django.core.checks import Error
from django.db import models


class BaseConstraint:
    """Base class for all constraints."""
    
    def __init__(self, name):
        self.name = name
    
    def check(self, model_class):
        """Check constraint for issues."""
        return []


class UniqueConstraint(BaseConstraint):
    """Unique constraint."""
    
    def __init__(self, fields, name, condition=None):
        super().__init__(name)
        self.fields = tuple(fields)
        self.condition = condition
    
    def check(self, model_class):
        """Check UniqueConstraint fields exist."""
        errors = []
        
        for field_name in self.fields:
            try:
                model_class._meta.get_field(field_name)
            except models.FieldDoesNotExist:
                errors.append(
                    Error(
                        "'UniqueConstraint' refers to the nonexistent field '%s'." % field_name,
                        obj=model_class,
                        id='models.E012',
                    )
                )
        
        return errors
    
    def __repr__(self):
        return f'<{self.__class__.__name__}: fields={self.fields} name={self.name}>'
    
    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.name == other.name and
            self.fields == other.fields and
            self.condition == other.condition
        )
