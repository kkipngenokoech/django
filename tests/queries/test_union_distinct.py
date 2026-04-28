import pytest
from django.db import NotSupportedError
from django.db import models
from django.db.models import Value, IntegerField
from django.test import TestCase
from django.contrib.auth.models import User


class Sample(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    """Test that distinct() on union queryset should raise NotSupportedError."""
    # Create test user
    user = User.objects.create_user('testuser', 'test@example.com', 'password')
    
    # Create test data
    Sample.objects.create(user=user, name="Sam1")
    Sample.objects.create(user=user, name="Sam2 acid")
    Sample.objects.create(user=user, name="Sam3")
    Sample.objects.create(user=user, name="Sam4 acid")
    Sample.objects.create(user=user, name="Dub")
    Sample.objects.create(user=user, name="Dub")
    Sample.objects.create(user=user, name="Dub")
    
    # Create querysets with annotations
    qs = Sample.objects.filter(user=user)
    qs1 = qs.filter(name='Dub').annotate(rank=Value(0, IntegerField()))
    qs2 = qs.filter(name='Sam1').annotate(rank=Value(1, IntegerField()))
    
    # Create union queryset
    union_qs = qs1.union(qs2)
    
    # This should raise NotSupportedError but currently doesn't
    with pytest.raises(NotSupportedError, match=r"Calling distinct\(\) after union\(\) is not supported"):
        union_qs.distinct()
    
    # Also test distinct with field names
    with pytest.raises(NotSupportedError, match=r"Calling distinct\(\) after union\(\) is not supported"):
        union_qs.distinct('name')
    
    # Test with intersection as well
    intersection_qs = qs1.intersection(qs2)
    with pytest.raises(NotSupportedError, match=r"Calling distinct\(\) after intersection\(\) is not supported"):
        intersection_qs.distinct()
    
    # Test with difference as well
    difference_qs = qs1.difference(qs2)
    with pytest.raises(NotSupportedError, match=r"Calling distinct\(\) after difference\(\) is not supported"):
        difference_qs.distinct()