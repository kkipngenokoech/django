from django.core.checks import Error, register
from django.db import models


@register('models')
def check_all_models(app_configs, **kwargs):
    """Check all models for various issues."""
    errors = []
    if app_configs is None:
        models_to_check = models.get_models()
    else:
        models_to_check = []
        for app_config in app_configs:
            models_to_check.extend(app_config.get_models())
    
    for model in models_to_check:
        errors.extend(_check_unique_constraints(model))
        errors.extend(_check_unique_together(model))
    
    return errors


def _check_unique_together(model):
    """Check unique_together option."""
    errors = []
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
