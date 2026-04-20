import pytest
from django.db import models
from django.db.models import Q, Count, OuterRef, Subquery
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
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
    ]
)
class GroupByAmbiguousColumnTest(TestCase):
    def setUp(self):
        # Create tables
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(A)
            schema_editor.create_model(B)
            schema_editor.create_model(AB)
            schema_editor.create_model(C)
    
    def test_group_by_annotated_subquery_no_ambiguity(self):
        """Test that GROUP BY uses full expression for annotated subqueries to avoid ambiguity."""
        # Create test data
        a_instance = A.objects.create()
        b_instance = B.objects.create()
        ab_instance = AB.objects.create(a=a_instance, b=b_instance, status=1)
        c_instance = C.objects.create(a=a_instance, status=2)
        
        # Reproduce the problematic query
        ab_query = AB.objects.filter(a=OuterRef("pk"), b=1)
        filter_conditions = Q(pk=1) | Q(ab_a__b=1)
        
        query = A.objects.filter(filter_conditions).annotate(
            status=Subquery(ab_query.values("status")),
            c_count=Count("c"),
        )
        
        # This should not raise a ProgrammingError about ambiguous column reference
        answer = query.values("status").annotate(total_count=Count("status"))
        
        # The query should execute without error
        result = list(answer)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['status'], 1)
        self.assertEqual(result[0]['total_count'], 1)
