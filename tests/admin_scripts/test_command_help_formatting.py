import io
from django.core.management.base import BaseCommand


def test_issue_reproduction():
    """Test that multi-line help text preserves formatting in command help output."""
    
    class TestCommand(BaseCommand):
        help = '''
        Import a contract from tzkt.
        Example usage:
            ./manage.py tzkt_import 'Tezos Mainnet' KT1HTDtMBRCKoNHjfWEEvXneGQpCfPAt6BRe
        '''
        
        def add_arguments(self, parser):
            parser.add_argument('blockchain', help='Name of the blockchain to import into')
            parser.add_argument('target', help='Id of the contract to import')
    
    # Capture the help output
    stdout = io.StringIO()
    command = TestCommand(stdout=stdout)
    
    # Generate help output
    command.print_help('manage.py', 'tzkt_import')
    help_output = stdout.getvalue()
    
    # The bug: help text should preserve newlines and indentation
    # Currently it strips them, making multi-line help unreadable
    assert 'Example usage:\n            ./manage.py' in help_output, f"Help formatting not preserved. Got: {repr(help_output)}"
    assert '        Import a contract from tzkt.\n        Example usage:' in help_output, f"Newlines not preserved. Got: {repr(help_output)}"