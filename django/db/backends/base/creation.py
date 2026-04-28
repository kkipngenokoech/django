import os
import sys
from io import StringIO

from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.db import router, transaction

# The prefix to put on the default database name when creating
# the test database.
TEST_DATABASE_PREFIX = 'test_'


class BaseDatabaseCreation:
    """
    Encapsulate backend-specific differences pertaining to creation and
    destruction of the test database.
    """
    def __init__(self, connection):
        self.connection = connection

    def _nodb_cursor(self):
        return self.connection._nodb_cursor()

    def log(self, msg):
        sys.stderr.write(msg + os.linesep)

    def create_test_db(self, verbosity=1, autoclobber=False, serialize=True, keepdb=False):
        """
        Create a test database, prompting the user for confirmation if the
        database already exists. Return the name of the test database created.
        """
        # Don't import django.core.management if it isn't needed.
        from django.core.management import call_command

        test_database_name = self._get_test_db_name()

        if verbosity >= 1:
            action = 'Creating'
            if keepdb:
                action = "Using existing"

            self.log('%s test database for alias %s...' % (
                action,
                self._get_database_display_str(verbosity, test_database_name),
            ))

        # We could skip this call if keepdb is True, but we instead
        # give it the keepdb param. This is to handle the case
        # where the test DB doesn't exist, in which case we need to
        # create it, then just not destroy it. If we instead skip
        # this, we will get an exception.
        self._create_test_db(verbosity, autoclobber, keepdb)

        self.connection.close()
        settings.DATABASES[self.connection.alias]["NAME"] = test_database_name
        self.connection.settings_dict["NAME"] = test_database_name

        if self.connection.settings_dict['TEST']['MIGRATE']:
            # We report migrate messages at one level lower than that
            # requested. This ensures we don't get flooded with messages during
            # testing (unless you really ask to be flooded).
            call_command(
                'migrate',
                verbosity=max(verbosity - 1, 0),
                interactive=False,
                database=self.connection.alias,
                run_syncdb=True,
            )

        # We then serialize the current state of the database into a string
        # and store it on the connection. This slightly horrific process is so people
        # who are testing on databases without transactions or who are using
        # a TransactionTestCase still get a clean database on every test run.
        if serialize:
            self.connection._test_serialized_contents = self.serialize_db_to_string()

        call_command('createcachetable', database=self.connection.alias)

        # Ensure a connection for the side effect of initializing the test database.
        self.connection.ensure_connection()

        return test_database_name

    def serialize_db_to_string(self):
        """
        Serialize all data in the database into a JSON string.
        Designed only for test runner usage; will not handle large
        amounts of data.
        """
        # Iteratively return every object for all models to serialize.
        def get_objects():
            from django.db.migrations.loader import MigrationLoader
            loader = MigrationLoader(self.connection)
            for app_config in apps.get_app_configs():
                if (
                    app_config.models_module is not None and
                    app_config.label in loader.migrated_apps and
                    app_config.name not in settings.TEST_NON_SERIALIZED_APPS
                ):
                    # Get all models for this app and sort them by dependencies
                    models = list(app_config.get_models())
                    
                    # Sort models to handle foreign key dependencies
                    # Models with no dependencies come first
                    sorted_models = []
                    remaining_models = models[:]
                    
                    while remaining_models:
                        # Find models with no unresolved dependencies
                        models_to_add = []
                        for model in remaining_models:
                            dependencies_resolved = True
                            for field in model._meta.get_fields():
                                if (hasattr(field, 'remote_field') and 
                                    field.remote_field and 
                                    field.remote_field.model and
                                    field.remote_field.model != model and
                                    field.remote_field.model in remaining_models):
                                    dependencies_resolved = False
                                    break
                            if dependencies_resolved:
                                models_to_add.append(model)
                        
                        if not models_to_add:
                            # Circular dependency or other issue, add remaining models
                            models_to_add = remaining_models[:]
                        
                        sorted_models.extend(models_to_add)
                        for model in models_to_add:
                            remaining_models.remove(model)
                    
                    for model in sorted_models:
                        if (not model._meta.proxy and router.allow_migrate_model(self.connection.alias, model)):
                            queryset = model._base_manager.using(self.connection.alias).order_by(model._meta.pk.name)
                            yield from queryset.iterator()
        
        out = StringIO()
        serializers.serialize("json", get_objects(), indent=None, stream=out)
        return out.getvalue()

    def deserialize_db_from_string(self, data):
        """
        Reload the database with data from a string generated by
        the serialize_db_to_string() method.
        """
        data = StringIO(data)
        
        # Load all objects first to handle dependencies
        objects_to_save = []
        for obj in serializers.deserialize("json", data, using=self.connection.alias):
            objects_to_save.append(obj)
        
        # Sort objects by model dependencies before saving
        # This ensures foreign key constraints are satisfied
        saved_models = set()
        remaining_objects = objects_to_save[:]
        
        while remaining_objects:
            objects_to_save_now = []
            for obj in remaining_objects:
                model = obj.object.__class__
                dependencies_satisfied = True
                
                # Check if all foreign key dependencies are satisfied
                for field in model._meta.get_fields():
                    if (hasattr(field, 'remote_field') and 
                        field.remote_field and 
                        field.remote_field.model and
                        field.remote_field.model != model and
                        field.remote_field.model not in saved_models):
                        dependencies_satisfied = False
                        break
                
                if dependencies_satisfied:
                    objects_to_save_now.append(obj)
            
            if not objects_to_save_now:
                # Handle circular dependencies or remaining objects
                objects_to_save_now = remaining_objects[:]
            
            # Save objects and track saved models
            for obj in objects_to_save_now:
                obj.save()
                saved_models.add(obj.object.__class__)
                remaining_objects.remove(obj)

    def _get_database_display_str(self, verbosity, database_name):
        """
        Return display string for a database for use in various actions.
        """
        return "'%s'%s" % (
            self.connection.alias,
            (" ('%s')" % database_name) if verbosity >= 2 else '',
        )

    def _get_test_db_name(self):
        """
        Internal implementation - return the name of the test DB that will be
        created. Only useful when called from create_test_db() and
        _create_test_db() and when no external munging is done with the 'NAME'
        settings.
        """
        if self.connection.settings_dict['TEST']['NAME']:
            return self.connection.settings_dict['TEST']['NAME']
        return TEST_DATABASE_PREFIX + self.connection.settings_dict['NAME']

    def _execute_create_test_db(self, cursor, parameters, keepdb=False):
        cursor.execute('CREATE DATABASE %(dbname)s %(suffix)s' % parameters)

    def _create_test_db(self, verbosity, autoclobber, keepdb=False):
        """
        Internal implementation - create the test db tables.
        """
        test_database_name = self._get_test_db_name()
        test_db_params = {
            'dbname': self.connection.ops.quote_name(test_database_name),
            'suffix': self.sql_table_creation_suffix(),
        }
        # Create the test database and connect to it.
        with self._nodb_cursor() as cursor:
            try:
                self._execute_create_test_db(cursor, test_db_params, keepdb)
            except Exception as e:
                # if we want to keep the db, then no need to do any of the below,
                # just return and skip it all.
                if keepdb:
                    return test_database_name
                
                self.log('Got an error creating the test database: %s' % e)
                if not autoclobber:
                    confirm = input(
                        "Type 'yes' if you would like to try deleting the test "
                        "database '%s', or 'no' to cancel: " % test_database_name
                    )
                if autoclobber or confirm == 'yes':
                    try:
                        if verbosity >= 1:
                            self.log('Destroying old test database for alias %s...' % (
                                self._get_database_display_str(verbosity, test_database_name),
                            ))
                        cursor.execute('DROP DATABASE %(dbname)s' % test_db_params)
                        self._execute_create_test_db(cursor, test_db_params, keepdb)
                    except Exception as e:
                        self.log('Got an error recreating the test database: %s' % e)
                        sys.exit(2)
                else:
                    self.log('Tests cancelled.')
                    sys.exit(1)

        return test_database_name

    def destroy_test_db(self, old_database_name, verbosity=1, keepdb=False, suffix=None):
        """
        Destroy a test database, prompting the user for confirmation if the
        database already exists.
        """
        self.connection.close()
        test_database_name = self.connection.settings_dict['NAME']
        if verbosity >= 1:
            action = 'Destroying'
            if keepdb:
                action = 'Preserving'
            self.log('%s test database for alias %s...' % (
                action,
                self._get_database_display_str(verbosity, test_database_name),
            ))

        # if we want to preserve the database
        # skip the actual destroying piece.
        if not keepdb:
            self._destroy_test_db(test_database_name, verbosity)

        # Restore the original database name
        settings.DATABASES[self.connection.alias]["NAME"] = old_database_name
        self.connection.settings_dict["NAME"] = old_database_name

    def _destroy_test_db(self, test_database_name, verbosity):
        """
        Internal implementation - remove the test db tables.
        """
        # Remove the test database to clean up after
        # ourselves. Connect to the previous database (not the test database)
        # to do so, because it's not allowed to delete a database while being
        # connected to it.
        with self._nodb_cursor() as cursor:
            cursor.execute("DROP DATABASE %s"
                           % self.connection.ops.quote_name(test_database_name))

    def sql_table_creation_suffix(self):
        """
        SQL to append to the end of the test table creation statements.
        """
        return ''

    def test_db_signature(self):
        """
        Return a tuple with elements of self.connection.settings_dict (a
        DATABASES setting value) that uniquely identify a database
        accordingly to the RDBMS particularities.
        """
        settings_dict = self.connection.settings_dict
        return (
            settings_dict['HOST'],
            settings_dict['PORT'],
            settings_dict['ENGINE'],
            self._get_test_db_name(),
        )