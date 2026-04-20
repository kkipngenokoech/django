import os
import tempfile
from django.test import TestCase, override_settings
from django.db import connections
from django.db.backends.sqlite3.creation import DatabaseCreation


class SQLiteMultiDBLockingTest(TestCase):
    """Test that reproduces and verifies fix for SQLite database locking with persistent test databases."""
    
    def test_keepdb_closes_connections_for_persistent_databases(self):
        """Test that keepdb=True closes connections for persistent SQLite databases to prevent locking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, 'test_db.sqlite3')
            
            # Configure a database with persistent test database
            test_databases = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': test_db_path,
                    'TEST': {
                        'NAME': test_db_path
                    },
                }
            }
            
            with override_settings(DATABASES=test_databases):
                conn = connections['default']
                creation = DatabaseCreation(conn)
                
                # Ensure connection exists
                conn.ensure_connection()
                self.assertTrue(conn.connection is not None)
                
                # Call _create_test_db with keepdb=True
                result = creation._create_test_db(verbosity=0, autoclobber=True, keepdb=True)
                
                # Verify the connection was closed for persistent database
                self.assertEqual(result, test_db_path)
                # Connection should be closed after keepdb handling
                self.assertTrue(conn.connection is None or conn.connection.closed)
    
    def test_keepdb_preserves_memory_database_connections(self):
        """Test that keepdb=True doesn't close connections for in-memory databases."""
        test_databases = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
                'TEST': {
                    'NAME': ':memory:'
                },
            }
        }
        
        with override_settings(DATABASES=test_databases):
            conn = connections['default']
            creation = DatabaseCreation(conn)
            
            # Call _create_test_db with keepdb=True for memory database
            result = creation._create_test_db(verbosity=0, autoclobber=True, keepdb=True)
            
            # Should return the shared memory database name
            self.assertTrue('mode=memory' in result)
            self.assertTrue('cache=shared' in result)
    
    def test_is_in_memory_db_detection(self):
        """Test the is_in_memory_db static method correctly identifies memory databases."""
        # Test various memory database formats
        self.assertTrue(DatabaseCreation.is_in_memory_db(':memory:'))
        self.assertTrue(DatabaseCreation.is_in_memory_db('file:memdb?mode=memory&cache=shared'))
        self.assertFalse(DatabaseCreation.is_in_memory_db('/path/to/file.db'))
        self.assertFalse(DatabaseCreation.is_in_memory_db('test.sqlite3'))
    
    def test_clone_db_closes_connections(self):
        """Test that _clone_test_db closes connections to prevent locking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_db = os.path.join(temp_dir, 'source.sqlite3')
            
            test_databases = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': source_db,
                }
            }
            
            with override_settings(DATABASES=test_databases):
                conn = connections['default']
                creation = DatabaseCreation(conn)
                
                # Create the source database
                conn.ensure_connection()
                with conn.cursor() as cursor:
                    cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY)')
                
                # Clone the database
                creation._clone_test_db('clone', verbosity=0, keepdb=False)
                
                # Verify connection was closed
                self.assertTrue(conn.connection is None or conn.connection.closed)
                
                # Verify clone was created
                clone_path = os.path.join(temp_dir, 'source_clone.sqlite3')
                self.assertTrue(os.path.exists(clone_path))