import itertools
import math
from copy import copy

from django.core.exceptions import EmptyResultSet
from django.db.models.expressions import Case, Exists, Func, Value, When
from django.db.models.fields import (
    BooleanField, CharField, DateTimeField, Field, IntegerField, UUIDField,
)
from django.db.models.query_utils import RegisterLookupMixin
from django.utils.datastructures import OrderedSet
from django.utils.functional import cached_property


class Lookup:
    lookup_name = None
    prepare_rhs = True
    can_use_none_as_rhs = False

    def __init__(self, lhs, rhs):
        self.lhs, self.rhs = lhs, rhs
        self.rhs = self.get_prep_lookup()
        if hasattr(self.lhs, 'get_bilateral_transforms'):
            bilateral_transforms = self.lhs.get_bilateral_transforms()
        else:
            bilateral_transforms = []
        if bilateral_transforms:
            # Warn the user as soon as possible if they are trying to apply
            # a bilateral transformation on a nested QuerySet: that won't work.
            from django.db.models.sql.query import Query  # avoid circular import
            if isinstance(rhs, Query):
                raise NotImplementedError("Bilateral transformations on nested querysets are not implemented.")
        self.bilateral_transforms = bilateral_transforms

    def apply_bilateral_transforms(self, value):
        for transform in self.bilateral_transforms:
            value = transform(value)
        return value

    def batch_process_rhs(self, compiler, connection, rhs=None):
        if rhs is None:
            rhs = self.rhs
        if self.bilateral_transforms:
            sqls, sqls_params = [], []
            for p in rhs:
                value = Value(p, output_field=self.lhs.output_field)
                value = self.apply_bilateral_transforms(value)
                value = value.resolve_expression(compiler.query)
                sql, sql_params = compiler.compile(value)
                sqls.append(sql)
                sqls_params.extend(sql_params)
        else:
            _, params = self.get_db_prep_lookup(rhs, connection)
            sqls, sqls_params = ['%s'] * len(params), params
        return sqls, sqls_params

    def get_source_expressions(self):
        if self.rhs_is_direct_value():
            return [self.lhs]
        return [self.lhs, self.rhs]

    def set_source_expressions(self, new_exprs):
        if len(new_exprs) == 1:
            self.lhs = new_exprs[0]
        else:
            self.lhs, self.rhs = new_exprs

    def get_prep_lookup(self):
        if hasattr(self.rhs, 'resolve_expression'):
            return self.rhs
        if self.prepare_rhs and hasattr(self.lhs.output_field, 'get_prep_value'):
            return self.lhs.output_field.get_prep_value(self.rhs)
        return self.rhs

    def get_db_prep_lookup(self, value, connection):
        return ('%s', [value])

    def process_lhs(self, compiler, connection, lhs=None):
        lhs = lhs or self.lhs
        if hasattr(lhs, 'resolve_expression'):
            lhs = lhs.resolve_expression(compiler.query)
        return compiler.compile(lhs)

    def process_rhs(self, compiler, connection):
        value = self.rhs
        if self.bilateral_transforms:
            if self.rhs_is_direct_value():
                # Do not call get_db_prep_lookup here as the value will be
                # transformed later in batch_process_rhs().
                value = Value(value, output_field=self.lhs.output_field)
                value = self.apply_bilateral_transforms(value)
                value = value.resolve_expression(compiler.query)
            return compiler.compile(value)
        else:
            if hasattr(value, 'resolve_expression'):
                value = value.resolve_expression(compiler.query)
                return compiler.compile(value)
            else:
                return self.get_db_prep_lookup(value, connection)

    def rhs_is_direct_value(self):
        return not hasattr(self.rhs, 'as_sql')

    def relabeled_clone(self, relabels):
        new = copy(self)
        new.lhs = new.lhs.relabeled_clone(relabels)
        if hasattr(new.rhs, 'relabeled_clone'):
            new.rhs = new.rhs.relabeled_clone(relabels)
        return new

    def get_group_by_cols(self, alias=None):
        cols = self.lhs.get_group_by_cols()
        if hasattr(self.rhs, 'get_group_by_cols'):
            cols.extend(self.rhs.get_group_by_cols())
        return cols

    def as_sql(self, compiler, connection):
        raise NotImplementedError('Subclasses must implement as_sql().')

    @cached_property
    def contains_aggregate(self):
        return self.lhs.contains_aggregate or getattr(self.rhs, 'contains_aggregate', False)

    @cached_property
    def contains_over_clause(self):
        return self.lhs.contains_over_clause or getattr(self.rhs, 'contains_over_clause', False)

    @property
    def is_summary(self):
        return self.lhs.is_summary or getattr(self.rhs, 'is_summary', False)


class Transform(RegisterLookupMixin, Func):
    """
    RegisterLookupMixin() is first so that get_lookup() and get_transform()
    first examine self and then check output_field.
    """
    bilateral = False
    arity = 1

    @property
    def lhs(self):
        return self.source_expressions[0]

    def get_bilateral_transforms(self):
        if hasattr(self.lhs, 'get_bilateral_transforms'):
            bilateral_transforms = self.lhs.get_bilateral_transforms()
        else:
            bilateral_transforms = []
        if self.bilateral:
            bilateral_transforms.append(self.__class__)
        return bilateral_transforms


class BuiltinLookup(Lookup):
    def process_lhs(self, compiler, connection, lhs=None):
        lhs_sql, params = super().process_lhs(compiler, connection, lhs)
        field_internal_type = self.lhs.output_field.get_internal_type()
        db_type = self.lhs.output_field.db_type(connection=connection)
        lhs_sql = connection.ops.field_cast_sql(
            db_type, field_internal_type) % lhs_sql
        lhs_sql = connection.ops.lookup_cast(self.lookup_name, field_internal_type) % lhs_sql
        return lhs_sql, list(params)

    def as_sql(self, compiler, connection):
        lhs_sql, params = self.process_lhs(compiler, connection)
        rhs_sql, rhs_params = self.process_rhs(compiler, connection)
        params.extend(rhs_params)
        return '%s %s %s' % (lhs_sql, self.operator, rhs_sql), params


class FieldGetDbPrepValueMixin:
    """
    Some lookups require Field.get_db_prep_value() to be called on their
    inputs.
    """
    get_db_prep_lookup_value_is_iterable = False

    def get_db_prep_lookup(self, value, connection):
        # For relational fields, use the 'target_field' attribute of the
        # output_field.
        field = getattr(self.lhs.output_field, 'target_field', None)
        get_db_prep_value = getattr(field, 'get_db_prep_value', None)
        if not get_db_prep_value:
            get_db_prep_value = self.lhs.output_field.get_db_prep_value
        return get_db_prep_value(value, connection, prepared=True)


class FieldGetDbPrepValueIterableMixin(FieldGetDbPrepValueMixin):
    """
    Some lookups require Field.get_db_prep_value() to be called on each value
    in an iterable.
    """
    get_db_prep_lookup_value_is_iterable = True

    def get_db_prep_lookup(self, value, connection):
        # For relational fields, use the 'target_field' attribute of the
        # output_field.
        field = getattr(self.lhs.output_field, 'target_field', None)
        get_db_prep_value = getattr(field, 'get_db_prep_value', None)
        if not get_db_prep_value:
            get_db_prep_value = self.lhs.output_field.get_db_prep_value
        return [
            get_db_prep_value(v, connection, prepared=True)
            for v in value
        ]

    def process_rhs(self, compiler, connection):
        if self.rhs_is_direct_value():
            # rhs should be an iterable of values. Use batch_process_rhs()
            # to prepare/transform those values.
            return self.batch_process_rhs(compiler, connection)
        else:
            return super().process_rhs(compiler, connection)


class PostgreSQLOverlap(Lookup):
    lookup_name = 'overlap'

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return '%s && %s' % (lhs, rhs), params


class DataContains(Lookup):
    lookup_name = 'contains'

    def as_sql(self, compiler, connection):
        if not connection.features.supports_json_field_contains:
            raise NotImplementedError(
                'contains lookup is not supported on this database backend.'
            )
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return 'JSON_CONTAINS(%s, %s)' % (lhs, rhs), params


class ContainedBy(Lookup):
    lookup_name = 'contained_by'

    def as_sql(self, compiler, connection):
        if not connection.features.supports_json_field_contains:
            raise NotImplementedError(
                'contained_by lookup is not supported on this database backend.'
            )
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return 'JSON_CONTAINS(%s, %s)' % (rhs, lhs), params


class Exact(FieldGetDbPrepValueMixin, BuiltinLookup):
    lookup_name = 'exact'
    operator = '='


class IExact(BuiltinLookup):
    lookup_name = 'iexact'
    operator = '='
    prepare_rhs = False

    def process_rhs(self, qn, connection):
        rhs, params = super().process_rhs(qn, connection)
        if params:
            params[0] = connection.ops.prep_for_iexact_query(params[0])
        return rhs, params


class GreaterThan(FieldGetDbPrepValueMixin, BuiltinLookup):
    lookup_name = 'gt'
    operator = '>'


class GreaterThanOrEqual(FieldGetDbPrepValueMixin, BuiltinLookup):
    lookup_name = 'gte'
    operator = '>='


class LessThan(FieldGetDbPrepValueMixin, BuiltinLookup):
    lookup_name = 'lt'
    operator = '<'


class LessThanOrEqual(FieldGetDbPrepValueMixin, BuiltinLookup):
    lookup_name = 'lte'
    operator = '<='


class IntegerFieldFloatRounding:
    """
    Allow floats to work as query values for IntegerField. Without this, the
    decimal portion of the float would always be discarded.
    """
    def get_prep_lookup(self):
        if isinstance(self.rhs, float):
            self.rhs = math.ceil(self.rhs)
        return super().get_prep_lookup()


class IntegerGreaterThanOrEqual(IntegerFieldFloatRounding, GreaterThanOrEqual):
    pass


class IntegerLessThan(IntegerFieldFloatRounding, LessThan):
    pass


class In(FieldGetDbPrepValueIterableMixin, BuiltinLookup):
    lookup_name = 'in'

    def process_rhs(self, compiler, connection):
        db_rhs = getattr(self.rhs, '_db', None)
        if db_rhs is not None and db_rhs != connection.alias:
            raise ValueError(
                "Subqueries aren't allowed across different databases. Force "
                "the inner query to be evaluated using `list(inner_query)`."
            )

        if self.rhs_is_direct_value():
            try:
                rhs = OrderedSet(self.rhs)
            except TypeError:  # Unhashable items in self.rhs
                rhs = self.rhs

            if not rhs:
                raise EmptyResultSet

            # rhs should be an iterable; use batch_process_rhs() to
            # prepare/transform those values.
            sqls, sqls_params = self.batch_process_rhs(compiler, connection, rhs)
            placeholder = '(' + ', '.join(sqls) + ')'
            return (placeholder, sqls_params)
        else:
            if not getattr(self.rhs, 'has_select_fields', True):
                self.rhs.clear_select_clause()
                self.rhs.add_field('pk')
            return super().process_rhs(compiler, connection)

    def as_sql(self, compiler, connection):
        max_in_list_size = connection.ops.max_in_list_size()
        if self.rhs_is_direct_value() and max_in_list_size and len(self.rhs) > max_in_list_size:
            return self.split_parameter_list_as_sql(compiler, connection)
        return super().as_sql(compiler, connection)

    def split_parameter_list_as_sql(self, compiler, connection):
        # This is a special case for Oracle which limits the number of parameters
        # that can be used in an "IN" query. If the limit is exceeded, then
        # logic is used to break up the "IN" query into smaller pieces.
        max_in_list_size = connection.ops.max_in_list_size()
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.batch_process_rhs(compiler, connection)
        in_clause_elements = ['('] + [rhs[0]] * max_in_list_size + [')']
        # Chop the parameter list into pieces of max_in_list_size.
        group_size = max_in_list_size
        if len(rhs_params) % group_size:
            extra_where_count = 1
        else:
            extra_where_count = 0
        where_count = len(rhs_params) // group_size + extra_where_count
        split_params = [rhs_params[i * group_size:(i + 1) * group_size] for i in range(where_count)]
        # Leave the last chunk out when it is of group_size to avoid an empty
        # IN clause.
        if split_params[-1] and len(split_params[-1]) == group_size:
            split_params[-1] = split_params[-1][:-1]
        conditions = []
        for param_chunk in split_params:
            if not param_chunk:
                continue
            in_clause_elements[1:-1] = [rhs[0]] * len(param_chunk)
            conditions.append('%s IN %s' % (lhs, ''.join(in_clause_elements)))
        return ' OR '.join(conditions), lhs_params + rhs_params

    operator = 'IN'

    def get_rhs_op(self, connection, rhs):
        return 'IN %s' % rhs


class PatternLookup(BuiltinLookup):
    param_pattern = '%%%s%%'
    prepare_rhs = False

    def get_rhs_op(self, connection, rhs):
        # Assume we are in startswith. We need to produce SQL like:
        #     col LIKE %s AND col < %s
        # For python values we can (and should) do that directly in Python,
        # but if we have a query expression we need to add other possibility.
        # Currently we only support startswith.
        return connection.pattern_ops[self.lookup_name] % rhs

    def process_rhs(self, qn, connection):
        rhs, params = super().process_rhs(qn, connection)
        if params and not hasattr(self.rhs, 'as_sql'):
            params[0] = self.param_pattern % connection.ops.prep_for_like_query(params[0])
        return rhs, params


class Contains(PatternLookup):
    lookup_name = 'contains'


class IContains(PatternLookup):
    lookup_name = 'icontains'


class StartsWith(PatternLookup):
    lookup_name = 'startswith'
    param_pattern = '%s%%'


class IStartsWith(PatternLookup):
    lookup_name = 'istartswith'
    param_pattern = '%s%%'


class EndsWith(PatternLookup):
    lookup_name = 'endswith'
    param_pattern = '%%%s'


class IEndsWith(PatternLookup):
    lookup_name = 'iendswith'
    param_pattern = '%%%s'


class Range(FieldGetDbPrepValueIterableMixin, BuiltinLookup):
    lookup_name = 'range'

    def get_rhs_op(self, connection, rhs):
        return "BETWEEN %s AND %s" % (rhs[0], rhs[1])


class IsNull(BuiltinLookup):
    lookup_name = 'isnull'
    prepare_rhs = False

    def __init__(self, lhs, rhs):
        # Validate that rhs is a boolean value
        if not isinstance(rhs, bool):
            raise ValueError(
                "The 'isnull' lookup only accepts boolean values (True or False), "
                f"got {type(rhs).__name__}: {rhs!r}"
            )
        super().__init__(lhs, rhs)

    def as_sql(self, compiler, connection):
        sql, params = compiler.compile(self.lhs)
        if self.rhs:
            return "%s IS NULL" % sql, params
        else:
            return "%s IS NOT NULL" % sql, params


class Regex(BuiltinLookup):
    lookup_name = 'regex'
    prepare_rhs = False

    def as_sql(self, compiler, connection):
        if self.lookup_name in connection.operators:
            return super().as_sql(compiler, connection)
        else:
            lhs, lhs_params = self.process_lhs(compiler, connection)
            rhs, rhs_params = self.process_rhs(compiler, connection)
            sql_template = connection.ops.regex_lookup(self.lookup_name)
            return sql_template % (lhs, rhs), lhs_params + rhs_params


class IRegex(Regex):
    lookup_name = 'iregex'


class YearLookup(Lookup):
    def year_lookup_bounds(self, connection, year):
        output_field = self.lhs.lhs.output_field
        if isinstance(output_field, DateTimeField):
            bounds = connection.ops.year_lookup_bounds_for_datetime_field(year)
        else:
            bounds = connection.ops.year_lookup_bounds_for_date_field(year)
        return bounds

    def as_sql(self, compiler, connection):
        # Avoid the extract operation if the rhs is a direct value to allow
        # indexes to be used.
        if self.rhs_is_direct_value():
            # Skip the extract part by directly using the originating field,
            # that is self.lhs.lhs.
            lhs_sql, params = self.process_lhs(compiler, connection, self.lhs.lhs)
            rhs_sql, rhs_params = self.process_rhs(compiler, connection)
            params.extend(rhs_params)
            bounds = self.year_lookup_bounds(connection, self.rhs)
            return '%s %s' % (lhs_sql, bounds), params
        return super().as_sql(compiler, connection)


class YearExact(YearLookup, Exact):
    def get_direct_rhs_sql(self, connection, rhs):
        return 'BETWEEN %s AND %s'

    def year_lookup_bounds(self, connection, year):
        bounds = super().year_lookup_bounds(connection, year)
        return 'BETWEEN %s AND %s' % bounds


class YearGt(YearLookup, GreaterThan):
    def get_bound(self, start, finish):
        return finish

    def year_lookup_bounds(self, connection, year):
        bounds = super().year_lookup_bounds(connection, year)
        return '> %s' % bounds[1]


class YearGte(YearLookup, GreaterThanOrEqual):
    def get_bound(self, start, finish):
        return start

    def year_lookup_bounds(self, connection, year):
        bounds = super().year_lookup_bounds(connection, year)
        return '>= %s' % bounds[0]


class YearLt(YearLookup, LessThan):
    def get_bound(self, start, finish):
        return start

    def year_lookup_bounds(self, connection, year):
        bounds = super().year_lookup_bounds(connection, year)
        return '< %s' % bounds[0]


class YearLte(YearLookup, LessThanOrEqual):
    def get_bound(self, start, finish):
        return finish

    def year_lookup_bounds(self, connection, year):
        bounds = super().year_lookup_bounds(connection, year)
        return '<= %s' % bounds[1]


class UUIDTextMixin:
    """
    Strip hyphens from a value when filtering a UUIDField on backends without
    a native datatype for UUID.
    """
    def process_rhs(self, qn, connection):
        if not connection.features.has_native_uuid_field:
            from django.db.models.fields import UUIDField
            if isinstance(self.rhs, UUIDField):
                self.rhs = self.rhs.hex
        return super().process_rhs(qn, connection)


Field.register_lookup(Exact)
Field.register_lookup(IExact)
Field.register_lookup(Contains)
Field.register_lookup(IContains)
Field.register_lookup(GreaterThan)
Field.register_lookup(GreaterThanOrEqual)
Field.register_lookup(LessThan)
Field.register_lookup(LessThanOrEqual)
Field.register_lookup(In)
Field.register_lookup(StartsWith)
Field.register_lookup(IStartsWith)
Field.register_lookup(EndsWith)
Field.register_lookup(IEndsWith)
Field.register_lookup(Range)
Field.register_lookup(IsNull)
Field.register_lookup(Regex)
Field.register_lookup(IRegex)

IntegerField.register_lookup(IntegerGreaterThanOrEqual)
IntegerField.register_lookup(IntegerLessThan)

Field.register_lookup(YearExact)
Field.register_lookup(YearGt)
Field.register_lookup(YearGte)
Field.register_lookup(YearLt)
Field.register_lookup(YearLte)