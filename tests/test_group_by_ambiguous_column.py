import pytest
from django.db import models
from django.db.models import Count, OuterRef, Q, Subquery
from django.test import TestCase
from django.db import connection
from django.test.utils import override_settings


class A(models.Model):
    bs = models.ManyToManyField('B', related_name="a", through="AB")
    
    class Meta:
        app_label = 'test_app'


class B(models.Model):
    class Meta:
        app_label = 'test_app'


class AB(models.Model):
    a = models.ForeignKey(A, on_delete=models.CASCADE, related_name="ab_a")
    b = models.ForeignKey(B, on_delete=models.CASCADE, related_name="ab_b")
    status = models.IntegerField()
    
    class Meta:
        app_label = 'test_app'


class C(models.Model):
    a = models.ForeignKey(
        A,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="c"
    )
    status = models.IntegerField()
    
    class Meta:
        app_label = 'test_app'


@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    INSTALLED_APPS=['test_app'],
    USE_TZ=False,
)
def test_issue_reproduction():
    """Test that reproduces the ambiguous column reference error in GROUP BY clauses."""
    
    # Create the tables
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(A)
        schema_editor.create_model(B)
        schema_editor.create_model(AB)
        schema_editor.create_model(C)
    
    try:
        # Create test data
        a_instance = A.objects.create()
        b_instance = B.objects.create()
        ab_instance = AB.objects.create(a=a_instance, b=b_instance, status=1)
        c_instance = C.objects.create(a=a_instance, status=2)
        
        # This is the exact query from the issue that should cause the error
        ab_query = AB.objects.filter(a=OuterRef("pk"), b=1)
        filter_conditions = Q(pk=1) | Q(ab_a__b=1)
        query = A.objects.\
            filter(filter_conditions).\
            annotate(
                status=Subquery(ab_query.values("status")),
                c_count=Count("c"),
            )
        
        # This should trigger the ambiguous column reference error
        answer = query.values("status").annotate(total_count=Count("status"))
        
        # Try to evaluate the query - this should raise ProgrammingError
        # about ambiguous column reference "status"
        list(answer)  # Force evaluation
        
        # If we get here without an exception, the bug is not reproduced
        pytest.fail("Expected ProgrammingError with ambiguous column reference, but query executed successfully")
        
    except Exception as e:
        # Check that we get the specific error mentioned in the issue
        error_msg = str(e).lower()
        assert "ambiguous" in error_msg and "status" in error_msg, f"Expected ambiguous status column error, got: {e}"
        
    finally:
        # Clean up tables
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(C)
            schema_editor.delete_model(AB)
            schema_editor.delete_model(B)
            schema_editor.delete_model(A)