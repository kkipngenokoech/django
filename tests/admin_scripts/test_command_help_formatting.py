import io
import sys
from django.core.management.base import BaseCommand


def test_issue_reproduction():
    """Test that multiline help text preserves formatting in command help output."""
    
    class TestCommand(BaseCommand):
        help = '''
        Import a contract from tzkt.
        Example usage:
            ./manage.py tzkt_import 'Tezos Mainnet' KT1HTDtMBRCKoNHjfWEEvXneGQpCfPAt6BRe
        '''
        
        def add_arguments(self, parser):
            parser.add_argument('blockchain', help='Name of the blockchain to import into')
            parser.add_argument('target', help='Id of the contract to import')
    
    # Capture help output
    captured_output = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured_output
    
    try:
        command = TestCommand()
        command.print_help('manage.py', 'tzkt_import')
        help_output = captured_output.getvalue()
    finally:
        sys.stdout = original_stdout
    
    # The bug: help text should preserve line breaks and indentation
    # Currently it gets flattened to a single line
    assert 'Import a contract from tzkt.\nExample usage:\n' in help_output, f"Help output should preserve line breaks, got: {repr(help_output)}"
    assert '    ./manage.py tzkt_import' in help_output, f"Help output should preserve indentation, got: {repr(help_output)}"