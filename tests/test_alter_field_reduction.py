import pytest
from django.db import migrations, models
from django.db.migrations.optimizer import MigrationOptimizer


def test_issue_reproduction():
    """Test that multiple AlterField operations on the same field are not reduced."""
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
    optimized = optimizer.optimize(operations, "books")
    
    # The bug: multiple AlterField operations should be reduced to a single one
    # but currently they are not reduced at all
    assert len(optimized) == 1, f"Expected 1 operation after optimization, got {len(optimized)}"
    assert isinstance(optimized[0], migrations.AlterField)
    assert optimized[0].field.max_length == 128
    assert optimized[0].field.help_text == "help"
    assert optimized[0].field.default is None