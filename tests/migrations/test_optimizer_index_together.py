import pytest
import warnings
from django.db import models
from django.db.migrations.operations.models import CreateModel, AlterModelOptions
from django.db.migrations.optimizer import MigrationOptimizer
from django.test import TestCase


def test_issue_reproduction():
    """Test that squashing migrations with index_together -> indexes transition removes deprecation warnings."""
    
    # Create a migration operation with index_together (deprecated)
    create_op = CreateModel(
        name="TestModel",
        fields=[
            ("id", models.AutoField(primary_key=True)),
            ("field1", models.CharField(max_length=100)),
            ("field2", models.CharField(max_length=100)),
        ],
        options={
            "index_together": [("field1", "field2")],
        },
    )
    
    # Create an operation that converts index_together to indexes
    alter_op = AlterModelOptions(
        name="TestModel",
        options={
            "indexes": [models.Index(fields=["field1", "field2"], name="test_idx")],
        },
    )
    
    # Test that the optimizer should combine these operations and remove index_together
    optimizer = MigrationOptimizer()
    operations = [create_op, alter_op]
    
    # Optimize the operations
    optimized = optimizer.optimize(operations, "testapp")
    
    # The optimized result should be a single CreateModel operation
    # with only 'indexes' and no 'index_together' to avoid deprecation warnings
    assert len(optimized) == 1
    assert isinstance(optimized[0], CreateModel)
    
    # This should pass after the fix - the optimized operation should not contain index_together
    # Currently this will fail because the optimizer doesn't handle the index_together -> indexes transition
    final_options = optimized[0].options
    
    # The bug: index_together is still present in the optimized operation, causing deprecation warnings
    assert "index_together" not in final_options, "index_together should be removed during optimization to avoid deprecation warnings"
    assert "indexes" in final_options, "indexes should be present in the optimized operation"