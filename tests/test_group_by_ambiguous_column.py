import pytest
from django.db import models
from django.db.models import Q, Count, OuterRef, Subquery
from django.test import TestCase
from django.db import connection
from django.core.management.color import no_style
from django.db import transaction


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


def test_issue_reproduction():
    # Create tables
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
        
        # This is the problematic query from the issue
        ab_query = AB.objects.filter(a=OuterRef("pk"), b=1)
        filter_conditions = Q(pk=1) | Q(ab_a__b=1)
        query = A.objects.filter(filter_conditions).annotate(
            status=Subquery(ab_query.values("status")),
            c_count=Count("c"),
        )
        answer = query.values("status").annotate(total_count=Count("status"))
        
        # This should raise ProgrammingError: column reference "status" is ambiguous
        list(answer)
        
    finally:
        # Clean up tables
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(C)
            schema_editor.delete_model(AB)
            schema_editor.delete_model(B)
            schema_editor.delete_model(A)