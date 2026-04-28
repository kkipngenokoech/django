import pytest
from django.db import models
from django.test import TestCase
from django.test.utils import override_settings


class Parent(models.Model):
    class Meta:
        app_label = 'test_app'
        ordering = ["-pk"]


class Child(Parent):
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    """Test that inherited model correctly orders by "-pk" when specified on Parent.Meta.ordering"""
    query = Child.objects.all().query
    sql, params = query.sql_with_params()
    
    # The query should contain ORDER BY with DESC, not ASC
    # Current bug: generates "ORDER BY "myapp_parent"."id" ASC" instead of DESC
    assert "DESC" in sql, f"Expected DESC ordering in SQL query, but got: {sql}"
    assert "ASC" not in sql or sql.count("DESC") > sql.count("ASC"), f"Expected descending order but query shows ascending: {sql}"