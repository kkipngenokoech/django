import pytest
from django.db import models, NotSupportedError
from django.db.models import Value, IntegerField
from django.test import TestCase
from django.contrib.auth.models import User


class Sample(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    # Create test data
    user = User.objects.create_user('testuser')
    Sample.objects.create(name='Dub', user=user)
    Sample.objects.create(name='Sam1', user=user)
    
    # Create union queryset with annotations
    qs = Sample.objects.filter(user=user)
    qs1 = qs.filter(name='Dub').annotate(rank=Value(0, IntegerField()))
    qs2 = qs.filter(name='Sam1').annotate(rank=Value(1, IntegerField()))
    union_qs = qs1.union(qs2)
    
    # This should raise NotSupportedError but currently doesn't
    with pytest.raises(NotSupportedError):
        union_qs.distinct('name')