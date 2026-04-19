import pytest
from django.db import models, transaction
from django.test import TestCase


class Product(models.Model):
    sku = models.CharField(primary_key=True, max_length=50)
    
    class Meta:
        app_label = 'test_app'


class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    """Test that demonstrates the foreign key data loss bug."""
    with transaction.atomic():
        order = Order()
        order.product = Product()  # Unsaved product with no primary key set
        order.product.sku = "foo"  # Set primary key after assignment
        order.product.save()
        order.save()
        
        # This should fail but currently succeeds - shows the bug
        assert not Order.objects.filter(product_id="").exists(), "Order should not have empty product_id"
        
        # This should succeed but currently fails - shows the bug  
        assert Order.objects.filter(product=order.product).exists(), "Order should reference the correct product"