from django.db import models
from django.test import TestCase
from django.test.utils import isolate_apps


class OrderingInheritanceTest(TestCase):
    """Test that inherited models correctly preserve ordering direction from parent."""
    
    def test_inherited_model_ordering_with_negative_pk(self):
        """Test that inherited model correctly orders by "-pk" from Parent.Meta.ordering"""
        
        @isolate_apps('test_app')
        def create_models():
            class Parent(models.Model):
                class Meta:
                    app_label = 'test_app'
                    ordering = ["-pk"]
            
            class Child(Parent):
                class Meta:
                    app_label = 'test_app'
            
            return Parent, Child
        
        Parent, Child = create_models()
        
        # Get the SQL query for Child.objects.all()
        query_str = str(Child.objects.all().query)
        
        # The bug: query should contain DESC ordering but shows ASC instead
        # Expected: ORDER BY "test_app_parent"."id" DESC
        # Actual: ORDER BY "test_app_parent"."id" ASC
        self.assertIn("DESC", query_str, f"Query should contain DESC ordering but got: {query_str}")
        self.assertNotIn("ASC", query_str, f"Query should not contain ASC ordering but got: {query_str}")
    
    def test_inherited_model_ordering_with_positive_pk(self):
        """Test that inherited model correctly orders by "pk" (positive) from Parent.Meta.ordering"""
        
        @isolate_apps('test_app')
        def create_models():
            class Parent(models.Model):
                class Meta:
                    app_label = 'test_app'
                    ordering = ["pk"]
            
            class Child(Parent):
                class Meta:
                    app_label = 'test_app'
            
            return Parent, Child
        
        Parent, Child = create_models()
        
        # Get the SQL query for Child.objects.all()
        query_str = str(Child.objects.all().query)
        
        # Should contain ASC ordering (or no explicit direction which defaults to ASC)
        # We check that it doesn't contain DESC
        self.assertNotIn("DESC", query_str, f"Query should not contain DESC ordering but got: {query_str}")
    
    def test_inherited_model_ordering_with_field_name(self):
        """Test that inherited model correctly orders by field names with direction"""
        
        @isolate_apps('test_app')
        def create_models():
            class Parent(models.Model):
                name = models.CharField(max_length=100)
                
                class Meta:
                    app_label = 'test_app'
                    ordering = ["-name"]
            
            class Child(Parent):
                class Meta:
                    app_label = 'test_app'
            
            return Parent, Child
        
        Parent, Child = create_models()
        
        # Get the SQL query for Child.objects.all()
        query_str = str(Child.objects.all().query)
        
        # Should contain DESC ordering for the name field
        self.assertIn("DESC", query_str, f"Query should contain DESC ordering but got: {query_str}")
