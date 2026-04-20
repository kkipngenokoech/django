import os
import shutil
import sys
from pathlib import Path

from django.db.backends.base.creation import BaseDatabaseCreation


class DatabaseCreation(BaseDatabaseCreation):

    @staticmethod
    def is_in_memory_db(database_name):
        return not isinstance(database_name, Path) and (
            database_name == ':memory:' or 'mode=memory' in database_name
        )

    def _get_test_db_name(self):
        test_database_name = self.connection.settings_dict['TEST']['NAME'] or ':memory:'
        if test_database_name == ':memory:':
            return 'file:memorydb_%s?mode=memory&cache=shared' % self.connection.alias
        return test_database_name

    def _create_test_db(self, verbosity, autoclobber, keepdb=False):
        test_database_name = self._get_test_db_name()

        if keepdb:
            # When keeping the database, ensure any existing connections are closed
            # to prevent "database is locked" errors with persistent SQLite files
            if not self.is_in_memory_db(test_database_name):
                # Close the current connection if it exists
                if hasattr(self.connection, 'close'):
                    self.connection.close()
            return test_database_name
        if not self.is_in_memory_db(test_database_name):
            # Erase the old test database
            if verbosity >= 1:
                self.log('Destroying old test database for alias %s...' % (
                    self._get_database_display_str(verbosity, test_database_name),
                ))
            if os.access(test_database_name, os.F_OK):
                if not autoclobber:
                    confirm = input(
                        "Type 'yes' if you would like to try deleting the test "
                        "database '%s', or 'no' to cancel: " % test_database_name
                    )
                if autoclobber or confirm == 'yes':
                    try:
                        os.remove(test_database_name)
                    except Exception as e:
                        self.log('Got an error deleting the old test database: %s' % e)
                        sys.exit(2)
                else:
                    self.log('Tests cancelled.')
                    sys.exit(1)
        return test_database_name

    def get_test_db_clone_settings(self, suffix):
        orig_settings_dict = self.connection.settings_dict
        source_database_name = orig_settings_dict['NAME']
        if self.is_in_memory_db(source_database_name):
            return orig_settings_dict
        else:
            root, ext = os.path.splitext(orig_settings_dict['NAME'])
            return {**orig_settings_dict, 'NAME': '{}_{}.{}'.format(root, suffix, ext)}

    def _clone_test_db(self, suffix, verbosity, keepdb=False):
        source_database_name = self.connection.settings_dict['NAME']
        target_database_name = self.get_test_db_clone_settings(suffix)['NAME']
        # Forking automatically makes a copy of an in-memory database
        if self.is_in_memory_db(source_database_name):
            return
        
        # Close any existing connections to prevent locking issues
        if hasattr(self.connection, 'close'):
            self.connection.close()
            
        if not keepdb:
            if verbosity >= 1:
                self.log('Cloning test database for alias %s...' % (
                    self._get_database_display_str(verbosity, target_database_name),
                ))
            try:
                shutil.copy(source_database_name, target_database_name)
            except Exception as e:
                self.log('Got an error cloning the test database: %s' % e)
                sys.exit(2)

    def _destroy_test_db(self, test_database_name, verbosity):
        if test_database_name and not self.is_in_memory_db(test_database_name):
            # Close connection before attempting to delete
            if hasattr(self.connection, 'close'):
                self.connection.close()
            # Remove the test database to clean up after the test run.
            if verbosity >= 1:
                self.log('Destroying test database for alias %s...' % (
                    self._get_database_display_str(verbosity, test_database_name),
                ))
            # The database file should be closed now, remove it.
            if os.access(test_database_name, os.F_OK):
                os.remove(test_database_name)