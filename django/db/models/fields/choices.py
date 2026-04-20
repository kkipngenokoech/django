from django.db.models.enums import get_choice_value

class FieldDescriptor:
    """Descriptor that ensures enum choices return primitive values"""
    def __init__(self, field):
        self.field = field
        self.name = field.name or 'field'
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        value = getattr(instance, f'_{self.name}', None)
        # Convert enum instances to primitive values
        return get_choice_value(value)
    
    def __set__(self, instance, value):
        # Store the original value (could be enum or primitive)
        setattr(instance, f'_{self.name}', value)

class CharField:
    """CharField that properly handles enum choices"""
    def __init__(self, max_length=None, choices=None, name=None):
        self.max_length = max_length
        self.choices = choices
        self.name = name
        self.descriptor = FieldDescriptor(self)
    
    def __set_name__(self, owner, name):
        self.name = name
        self.descriptor.name = name
    
    def __get__(self, instance, owner):
        return self.descriptor.__get__(instance, owner)
    
    def __set__(self, instance, value):
        self.descriptor.__set__(instance, value)
    
    def to_python(self, value):
        if value is None:
            return value
        # Convert enum instances to their string values
        primitive_value = get_choice_value(value)
        return str(primitive_value)
    
    def validate(self, value):
        if self.choices and value is not None:
            primitive_value = get_choice_value(value)
            valid_choices = [choice[0] if isinstance(choice, tuple) else choice for choice in self.choices]
            if primitive_value not in valid_choices:
                raise ValueError(f"Value '{primitive_value}' is not a valid choice")

class IntegerField:
    """IntegerField that properly handles enum choices"""
    def __init__(self, choices=None, name=None):
        self.choices = choices
        self.name = name
        self.descriptor = FieldDescriptor(self)
    
    def __set_name__(self, owner, name):
        self.name = name
        self.descriptor.name = name
    
    def __get__(self, instance, owner):
        return self.descriptor.__get__(instance, owner)
    
    def __set__(self, instance, value):
        self.descriptor.__set__(instance, value)
    
    def to_python(self, value):
        if value is None:
            return value
        # Convert enum instances to their integer values
        primitive_value = get_choice_value(value)
        return int(primitive_value)
    
    def validate(self, value):
        if self.choices and value is not None:
            primitive_value = get_choice_value(value)
            valid_choices = [choice[0] if isinstance(choice, tuple) else choice for choice in self.choices]
            if primitive_value not in valid_choices:
                raise ValueError(f"Value '{primitive_value}' is not a valid choice")
