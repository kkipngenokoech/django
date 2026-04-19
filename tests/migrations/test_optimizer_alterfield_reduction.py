import pytest
from django.db import migrations, models
from django.db.migrations.optimizer import MigrationOptimizer


def test_issue_reproduction():
    """Test that multiple AlterField operations on the same field are reduced to a single operation."""
    operations = [
        migrations.AlterField(
            model_name="book",
            name="title",
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name="book",
            name="title",
            field=models.CharField(max_length=128, null=True, help_text="help"),
        ),
        migrations.AlterField(
            model_name="book",
            name="title",
            field=models.CharField(max_length=128, null=True, help_text="help", default=None),
        ),
    ]
    
    optimizer = MigrationOptimizer()
    optimized_operations = optimizer.optimize(operations, "books")
    
    # The bug: currently returns 3 operations, should return 1
    # Multiple AlterField operations on the same field should be reduced to the final one
    assert len(optimized_operations) == 1, f"Expected 1 operation, got {len(optimized_operations)}"
    
    # Verify the final operation has the correct field configuration
    final_op = optimized_operations[0]
    assert isinstance(final_op, migrations.AlterField)
    assert final_op.model_name == "book"
    assert final_op.name == "title"
    assert final_op.field.max_length == 128
    assert final_op.field.null is True
    assert final_op.field.help_text == "help"
    assert final_op.field.default is None