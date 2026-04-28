import pytest
from django.db import models
from django.db.models.fields import AutoFieldMeta
from django.test import override_settings
from django.apps import apps
from django.conf import settings


class MyBigAutoField(models.BigAutoField):
    pass


class MySmallAutoField(models.SmallAutoField):
    pass


def test_issue_reproduction():
    """Test that subclasses of BigAutoField and SmallAutoField are recognized as AutoField subclasses."""
    # Test that the AutoFieldMeta.__subclasscheck__ correctly identifies
    # subclasses of BigAutoField and SmallAutoField as AutoField subclasses
    
    # This should pass but currently fails due to the bug
    assert issubclass(MyBigAutoField, models.AutoField), "MyBigAutoField should be recognized as AutoField subclass"
    assert issubclass(MySmallAutoField, models.AutoField), "MySmallAutoField should be recognized as AutoField subclass"
    
    # Test the actual scenario from the issue - using DEFAULT_AUTO_FIELD
    with override_settings(DEFAULT_AUTO_FIELD='test_django_autofield_subclass.MyBigAutoField'):
        # This would normally trigger the validation during model creation
        # The validation happens in Options._get_default_pk_class()
        from django.db.models.options import Options
        opts = Options(meta=None)
        
        # This should not raise ValueError but currently does
        try:
            pk_class = opts._get_default_pk_class()
            # If we get here, the validation passed
            assert issubclass(pk_class, models.AutoField)
        except ValueError as e:
            if "must subclass AutoField" in str(e):
                pytest.fail(f"DEFAULT_AUTO_FIELD validation failed for BigAutoField subclass: {e}")
            else:
                raise