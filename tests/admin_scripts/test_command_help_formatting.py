import io
import sys
from django.core.management.base import BaseCommand


def test_issue_reproduction():
    """Test that management command help preserves multi-line formatting with indentation."""
    
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
        parser = command.create_parser('manage.py', 'tzkt_import')
        parser.print_help()
        help_output = captured_output.getvalue()
    finally:
        sys.stdout = original_stdout
    
    # The help should preserve the multi-line formatting with proper line breaks
    # This assertion will FAIL on current code because formatting is stripped
    assert 'Import a contract from tzkt.\nExample usage:\n    ./manage.py tzkt_import' in help_output