import pytest
from django.db import models
from django.test import TestCase
from django.test.utils import override_settings


class Publication(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_app'


class Article(models.Model):
    title = models.CharField(max_length=100)
    publications = models.ManyToManyField(Publication, blank=True)
    
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
class TestQuerySetNoneOnCombinedQueries(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from django.core.management.color import no_style
        from django.db import connection
        
        style = no_style()
        sql = connection.ops.sql_table_creation_suffix()
        
        # Create tables manually since we're using a test model
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(Publication)
            schema_editor.create_model(Article)
    
    def setUp(self):
        # Create test data
        self.pub1 = Publication.objects.create(name='Pub 1')
        self.pub2 = Publication.objects.create(name='Pub 2') 
        self.pub3 = Publication.objects.create(name='Pub 3')
        self.pub4 = Publication.objects.create(name='Pub 4')
        self.pub5 = Publication.objects.create(name='Pub 5')
        self.pub6 = Publication.objects.create(name='Pub 6')
        self.pub7 = Publication.objects.create(name='Pub 7')
    
    def test_issue_reproduction(self):
        # Test the OR query behavior (this should work correctly)
        or_queryset = Publication.objects.filter(id__lt=2) | Publication.objects.filter(id__gt=5)
        or_none_queryset = or_queryset.none()
        
        # This should return 0 results
        or_none_count = or_none_queryset.count()
        assert or_none_count == 0, f"OR queryset none() should return 0 results, got {or_none_count}"
        
        # Test the union query behavior (this is the bug)
        union_queryset = Publication.objects.filter(id__lt=2).union(
            Publication.objects.filter(id__gt=5)
        )
        union_none_queryset = union_queryset.none()
        
        # This should return 0 results but currently returns all matching results
        union_none_count = union_none_queryset.count()
        assert union_none_count == 0, f"Union queryset none() should return 0 results, got {union_none_count}"