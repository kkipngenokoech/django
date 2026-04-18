import unittest
from unittest.mock import Mock, patch
from io import StringIO

from django.core.management import call_command
from django.core.management.commands.inspectdb import Command
from django.db import connection
from django.test import TestCase, TransactionTestCase


class InspectDBRelatedNameTests(TransactionTestCase):
    """
    Tests for inspectdb command's automatic related_name generation
    when multiple foreign keys reference the same model.
    """
    
    def setUp(self):
        self.command = Command()
        
    def test_multiple_fks_to_same_table_generates_related_name(self):
        """
        Test that when multiple foreign keys reference the same table,
        related_name is automatically generated.
        """
        # Mock database introspection data
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.introspection.get_table_list.return_value = [
            Mock(name='test_table', type='t')
        ]
        mock_connection.introspection.get_relations.return_value = {
            'user_id': ('id', 'auth_user'),
            'manager_id': ('id', 'auth_user'),
        }
        mock_connection.introspection.get_constraints.return_value = {}
        mock_connection.introspection.get_primary_key_columns.return_value = ['id']
        mock_connection.introspection.get_primary_key_column.return_value = 'id'
        mock_connection.introspection.get_table_description.return_value = [
            Mock(name='id', type_code=1, null_ok=False),
            Mock(name='user_id', type_code=1, null_ok=True),
            Mock(name='manager_id', type_code=1, null_ok=True),
        ]
        mock_connection.features.introspected_field_types = {'AutoField': 'AutoField'}
        
        with patch('django.core.management.commands.inspectdb.connections') as mock_connections:
            mock_connections.__getitem__.return_value = mock_connection
            
            options = {
                'database': 'default',
                'table': ['test_table'],
                'include_partitions': False,
                'include_views': False,
            }
            
            output = list(self.command.handle_inspection(options))
            
        # Convert output to string for easier assertion
        output_str = '\n'.join(output)
        
        # Check that related_name is added for both foreign keys
        self.assertIn("related_name='user'", output_str)
        self.assertIn("related_name='manager'", output_str)
        
    def test_single_fk_no_related_name(self):
        """
        Test that when only one foreign key references a table,
        no related_name is generated.
        """
        # Mock database introspection data
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.introspection.get_table_list.return_value = [
            Mock(name='test_table', type='t')
        ]
        mock_connection.introspection.get_relations.return_value = {
            'user_id': ('id', 'auth_user'),
        }
        mock_connection.introspection.get_constraints.return_value = {}
        mock_connection.introspection.get_primary_key_columns.return_value = ['id']
        mock_connection.introspection.get_primary_key_column.return_value = 'id'
        mock_connection.introspection.get_table_description.return_value = [
            Mock(name='id', type_code=1, null_ok=False),
            Mock(name='user_id', type_code=1, null_ok=True),
        ]
        mock_connection.features.introspected_field_types = {'AutoField': 'AutoField'}
        
        with patch('django.core.management.commands.inspectdb.connections') as mock_connections:
            mock_connections.__getitem__.return_value = mock_connection
            
            options = {
                'database': 'default',
                'table': ['test_table'],
                'include_partitions': False,
                'include_views': False,
            }
            
            output = list(self.command.handle_inspection(options))
            
        # Convert output to string for easier assertion
        output_str = '\n'.join(output)
        
        # Check that no related_name is added
        self.assertNotIn("related_name=", output_str)
        
    def test_self_referencing_fk_with_multiple_fields(self):
        """
        Test that self-referencing foreign keys with multiple fields
        get appropriate related_name values.
        """
        # Mock database introspection data
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.introspection.get_table_list.return_value = [
            Mock(name='test_table', type='t')
        ]
        mock_connection.introspection.get_relations.return_value = {
            'parent_id': ('id', 'test_table'),
            'supervisor_id': ('id', 'test_table'),
        }
        mock_connection.introspection.get_constraints.return_value = {}
        mock_connection.introspection.get_primary_key_columns.return_value = ['id']
        mock_connection.introspection.get_primary_key_column.return_value = 'id'
        mock_connection.introspection.get_table_description.return_value = [
            Mock(name='id', type_code=1, null_ok=False),
            Mock(name='parent_id', type_code=1, null_ok=True),
            Mock(name='supervisor_id', type_code=1, null_ok=True),
        ]
        mock_connection.features.introspected_field_types = {'AutoField': 'AutoField'}
        
        with patch('django.core.management.commands.inspectdb.connections') as mock_connections:
            mock_connections.__getitem__.return_value = mock_connection
            
            options = {
                'database': 'default',
                'table': ['test_table'],
                'include_partitions': False,
                'include_views': False,
            }
            
            output = list(self.command.handle_inspection(options))
            
        # Convert output to string for easier assertion
        output_str = '\n'.join(output)
        
        # Check that related_name is added for both self-referencing foreign keys
        self.assertIn("related_name='parent'", output_str)
        self.assertIn("related_name='supervisor'", output_str)
        
    def test_mixed_relationship_types(self):
        """
        Test that both ForeignKey and OneToOneField relationships
        get related_name when multiple fields reference the same table.
        """
        # Mock database introspection data
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.introspection.get_table_list.return_value = [
            Mock(name='test_table', type='t')
        ]
        mock_connection.introspection.get_relations.return_value = {
            'user_id': ('id', 'auth_user'),
            'profile_id': ('id', 'auth_user'),  # This will be OneToOne due to unique constraint
        }
        mock_connection.introspection.get_constraints.return_value = {
            'unique_profile': {'unique': True, 'columns': ['profile_id']}
        }
        mock_connection.introspection.get_primary_key_columns.return_value = ['id']
        mock_connection.introspection.get_primary_key_column.return_value = 'id'
        mock_connection.introspection.get_table_description.return_value = [
            Mock(name='id', type_code=1, null_ok=False),
            Mock(name='user_id', type_code=1, null_ok=True),
            Mock(name='profile_id', type_code=1, null_ok=True),
        ]
        mock_connection.features.introspected_field_types = {'AutoField': 'AutoField'}
        
        with patch('django.core.management.commands.inspectdb.connections') as mock_connections:
            mock_connections.__getitem__.return_value = mock_connection
            
            options = {
                'database': 'default',
                'table': ['test_table'],
                'include_partitions': False,
                'include_views': False,
            }
            
            output = list(self.command.handle_inspection(options))
            
        # Convert output to string for easier assertion
        output_str = '\n'.join(output)
        
        # Check that related_name is added for both relationship types
        self.assertIn("related_name='user'", output_str)
        self.assertIn("related_name='profile'", output_str)
        
    def test_three_fks_to_same_table(self):
        """
        Test that when three or more foreign keys reference the same table,
        all get appropriate related_name values.
        """
        # Mock database introspection data
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.introspection.get_table_list.return_value = [
            Mock(name='test_table', type='t')
        ]
        mock_connection.introspection.get_relations.return_value = {
            'created_by_id': ('id', 'auth_user'),
            'updated_by_id': ('id', 'auth_user'),
            'approved_by_id': ('id', 'auth_user'),
        }
        mock_connection.introspection.get_constraints.return_value = {}
        mock_connection.introspection.get_primary_key_columns.return_value = ['id']
        mock_connection.introspection.get_primary_key_column.return_value = 'id'
        mock_connection.introspection.get_table_description.return_value = [
            Mock(name='id', type_code=1, null_ok=False),
            Mock(name='created_by_id', type_code=1, null_ok=True),
            Mock(name='updated_by_id', type_code=1, null_ok=True),
            Mock(name='approved_by_id', type_code=1, null_ok=True),
        ]
        mock_connection.features.introspected_field_types = {'AutoField': 'AutoField'}
        
        with patch('django.core.management.commands.inspectdb.connections') as mock_connections:
            mock_connections.__getitem__.return_value = mock_connection
            
            options = {
                'database': 'default',
                'table': ['test_table'],
                'include_partitions': False,
                'include_views': False,
            }
            
            output = list(self.command.handle_inspection(options))
            
        # Convert output to string for easier assertion
        output_str = '\n'.join(output)
        
        # Check that related_name is added for all three foreign keys
        self.assertIn("related_name='created_by'", output_str)
        self.assertIn("related_name='updated_by'", output_str)
        self.assertIn("related_name='approved_by'", output_str)
