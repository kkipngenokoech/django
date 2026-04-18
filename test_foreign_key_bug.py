import pytest
from django.db import models, transaction
from django.test import TestCase
from django.db import connection


class Product(models.Model):
    sku = models.CharField(primary_key=True, max_length=50)
    
    class Meta:
        app_label = 'test_app'


class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    # Create tables for our test models
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Product)
        schema_editor.create_model(Order)
    
    try:
        with transaction.atomic():
            order = Order()
            order.product = Product()  # Assign unsaved Product instance
            order.product.sku = "foo"  # Set primary key after assignment
            order.product.save()
            order.save()
            
            # This assertion should fail but currently passes (the bug)
            # The order's product_id should be "foo" but is actually ""
            assert not Order.objects.filter(product_id="").exists(), "Order should not have empty product_id"
            
            # This assertion should pass but currently fails
            assert Order.objects.filter(product=order.product).exists(), "Order should be linked to the product"
    finally:
        # Clean up tables
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(Order)
            schema_editor.delete_model(Product)