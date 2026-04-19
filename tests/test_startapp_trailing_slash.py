import os
import tempfile
from django.core.management.base import CommandError
from django.core.management.templates import TemplateCommand
import pytest


def test_issue_reproduction():
    """Test that startapp fails with trailing slash in directory name."""
    # Create a temporary directory to use as target
    with tempfile.TemporaryDirectory() as temp_dir:
        # Add trailing slash to the directory path
        target_with_slash = temp_dir + os.sep
        
        # Create TemplateCommand instance
        command = TemplateCommand()
        
        # This should raise CommandError due to the trailing slash bug
        with pytest.raises(CommandError, match="'' is not a valid app directory"):
            command.handle('app', 'myapp', target=target_with_slash)