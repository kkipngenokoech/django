import pytest
from django.db.backends.postgresql.client import DatabaseClient


def test_issue_reproduction():
    """Test that additional parameters are placed before database name in PostgreSQL client."""
    settings_dict = {
        'NAME': 'test_db',
        'USER': 'test_user',
        'HOST': 'localhost',
        'PORT': '5432',
    }
    
    # Additional parameters that should come before the database name
    parameters = ['-c', 'select * from some_table;']
    
    args, env = DatabaseClient.settings_to_cmd_args_env(settings_dict, parameters)
    
    # Find the positions of database name and the additional parameters
    db_name_index = args.index('test_db')
    c_flag_index = args.index('-c')
    
    # The -c flag should come before the database name
    # This assertion will FAIL on the current buggy code where parameters are appended after dbname
    assert c_flag_index < db_name_index, f"Parameters should come before database name. Got args: {args}"