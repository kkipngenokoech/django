import os
import tempfile
from django.core.management.base import CommandError
from django.core.management.templates import TemplateCommand
import pytest


def test_issue_reproduction():
    """Test that startapp fails with trailing slash in directory name."""
    # Create a temporary directory to use as target
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the target directory with a valid name
        target_dir = os.path.join(temp_dir, "myapp")
        os.makedirs(target_dir)
        
        # Add trailing slash to simulate bash tab-completion
        target_with_slash = target_dir + os.sep
        
        # Create TemplateCommand instance
        command = TemplateCommand()
        command.app_or_project = 'app'
        command.a_or_an = 'an'
        
        # This should raise CommandError due to the trailing slash bug
        with pytest.raises(CommandError, match="'' is not a valid app directory"):
            command.handle('app', 'myapp', target=target_with_slash)