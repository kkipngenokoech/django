import inspect
import types
from collections import defaultdict
from itertools import chain

from django.apps import apps
from django.core.checks import Error, Tags, register
from django.db import router


@register(Tags.models)
def check_all_models(app_configs=None, **kwargs):
    # Group models by database and table name to allow same table names across different databases
    db_table_models = defaultdict(lambda: defaultdict(list))
    indexes = defaultdict(list)
    constraints = defaultdict(list)
    errors = []
    if app_configs is None:
        models = apps.get_models()
    else:
        models = chain.from_iterable(app_config.get_models() for app_config in app_configs)
    for model in models:
        if model._meta.managed and not model._meta.proxy:
            # Determine which database this model uses
            db_alias = router.db_for_read(model)
            if db_alias is None:
                db_alias = 'default'
            db_table_models[db_alias][model._meta.db_table].append(model._meta.label)
        if not inspect.ismethod(model.check):
            errors.append(
                Error(
                    "The '%s.check()' class method is currently overridden by %r."
                    % (model.__name__, model.check),
                    obj=model,
                    id='models.E020'
                )
            )
        else:
            errors.extend(model.check(**kwargs))
        for model_index in model._meta.indexes:
            indexes[model_index.name].append(model._meta.label)
        for model_constraint in model._meta.constraints:
            constraints[model_constraint.name].append(model._meta.label)
    
    # Check for duplicate table names within each database
    for db_alias, tables in db_table_models.items():
        for db_table, model_labels in tables.items():
            if len(model_labels) != 1:
                errors.append(
                    Error(
                        "db_table '%s' is used by multiple models: %s."
                        % (db_table, ', '.join(model_labels)),
                        obj=db_table,
                        id='models.E028',
                    )
                )
    
    for index_name, model_labels in indexes.items():
        if len(model_labels) > 1:
            model_labels = set(model_labels)
            errors.append(
                Error(
                    "index name '%s' is not unique %s %s." % (
                        index_name,
                        'for model' if len(model_labels) == 1 else 'amongst models:',
                        ', '.join(sorted(model_labels)),
                    ),
                    id='models.E029' if len(model_labels) == 1 else 'models.E030',
                ),
            )
    for constraint_name, model_labels in constraints.items():
        if len(model_labels) > 1:
            model_labels = set(model_labels)
            errors.append(
                Error(
                    "constraint name '%s' is not unique amongst models: %s."
                    % (constraint_name, ', '.join(sorted(model_labels))),
                    id='models.E031',
                ),
            )
    return errors