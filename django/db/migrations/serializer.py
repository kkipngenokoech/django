import builtins
import collections.abc
import datetime
import decimal
import enum
import functools
import math
import re
import types
import uuid
import importlib

from django.conf import SettingsReference
from django.db import models
from django.db.migrations.operations.base import Operation
from django.db.migrations.utils import COMPILED_REGEX_TYPE, RegexObject
from django.utils.functional import LazyObject, Promise
from django.utils.timezone import utc
from django.utils.version import get_docs_version


class BaseSerializer:
    def __init__(self, value):
        self.value = value

    def serialize(self):
        raise NotImplementedError('Subclasses of BaseSerializer must implement the serialize() method.')


class BaseSequenceSerializer(BaseSerializer):
    def _format(self):
        raise NotImplementedError('Subclasses of BaseSequenceSerializer must implement the _format() method.')

    def serialize(self):
        imports = set()
        strings = []
        for item in self.value:
            item_string, item_imports = serializer_factory(item).serialize()
            imports.update(item_imports)
            strings.append(item_string)
        value = self._format()
        return value % (", ".join(strings)), imports


class BaseSimpleSerializer(BaseSerializer):
    def serialize(self):
        return repr(self.value), set()


class ChoicesSerializer(BaseSerializer):
    def serialize(self):
        return serializer_factory(self.value.value).serialize()


class DateTimeSerializer(BaseSerializer):
    """For datetime.*, except datetime.datetime."""
    def serialize(self):
        return repr(self.value), {'import datetime'}


class DatetimeDatetimeSerializer(BaseSerializer):
    """For datetime.datetime."""
    def serialize(self):
        if self.value.tzinfo is not None and self.value.tzinfo != utc:
            self.value = self.value.astimezone(utc)
        imports = ["import datetime"]
        if self.value.tzinfo is not None:
            imports.append("from django.utils.timezone import utc")
        return repr(self.value).replace('<UTC>', 'utc'), set(imports)


class DecimalSerializer(BaseSerializer):
    def serialize(self):
        return repr(self.value), {"from decimal import Decimal"}


class DeconstructableSerializer(BaseSerializer):
    @staticmethod
    def serialize_deconstructed(path, args, kwargs):
        name, imports = DeconstructableSerializer._serialize_path(path)
        strings = []
        for arg in args:
            arg_string, arg_imports = serializer_factory(arg).serialize()
            strings.append(arg_string)
            imports.update(arg_imports)
        for kw, arg in sorted(kwargs.items()):
            arg_string, arg_imports = serializer_factory(arg).serialize()
            imports.update(arg_imports)
            strings.append("%s=%s" % (kw, arg_string))
        return "%s(%s)" % (name, ", ".join(strings)), imports

    @staticmethod
    def _serialize_path(path):
        # Handle inner classes by preserving the full dotted path
        module, name = path.rsplit('.', 1)
        
        # Check if this is a local class (contains '<locals>')
        if '<locals>' in module:
            # For local classes, we need to extract the outer class names
            # Example: 'test_module.test_func.<locals>.Outer.Inner' -> 'Outer.Inner'
            locals_index = module.find('<locals>')
            if locals_index != -1:
                # Get everything after '<locals>.'
                after_locals = module[locals_index + len('<locals>.'):]n                if after_locals:
                    # Combine the outer class path with the final name
                    name = after_locals + '.' + name
                # Return just the class name without module import
                return name, set()
        
        # For regular module-level classes, import the module
        try:
            importlib.import_module(module)
            return name, {"import %s" % module}
        except ImportError:
            # If we can't import the module, return the full path
            return path, set()

    def serialize(self):
        return self.serialize_deconstructed(*self.value.deconstruct())


class DictionarySerializer(BaseSequenceSerializer):
    def _format(self):
        return "{%s}"


class EnumSerializer(BaseSerializer):
    def serialize(self):
        enum_class = self.value.__class__
        module = enum_class.__module__
        return (
            "%s.%s[%r]" % (module, enum_class.__qualname__, self.value.name),
            {"import %s" % module}
        )


class FloatSerializer(BaseSimpleSerializer):
    def serialize(self):
        if math.isnan(self.value) or math.isinf(self.value):
            return 'float("%s")' % self.value, set()
        return super().serialize()


class FrozensetSerializer(BaseSequenceSerializer):
    def _format(self):
        return "frozenset([%s])"


class FunctionTypeSerializer(BaseSerializer):
    def serialize(self):
        if getattr(self.value, "__self__", None) and isinstance(self.value.__self__, type):
            klass = self.value.__self__
            module = klass.__module__
            return "%s.%s.%s" % (module, klass.__name__, self.value.__name__), {"import %s" % module}
        # Further error checking
        if self.value.__name__ == '<lambda>':
            raise ValueError("Cannot serialize function: lambda")
        if self.value.__module__ is None:
            raise ValueError("Cannot serialize function %r: No module" % self.value)

        module_name = self.value.__module__

        if '<locals>' in self.value.__qualname__:
            raise ValueError(
                "Cannot serialize function %r: it's a local function. Please "
                "move it to the top level of the module." % self.value
            )

        return "%s.%s" % (module_name, self.value.__qualname__), {"import %s" % module_name}


class FunctoolsPartialSerializer(BaseSerializer):
    def serialize(self):
        # Serialize functools.partial objects
        func_string, func_imports = serializer_factory(self.value.func).serialize()
        args_string, args_imports = serializer_factory(self.value.args).serialize()
        keywords_string, keywords_imports = serializer_factory(self.value.keywords).serialize()
        # Note that we always use functools.partial name directly
        return (
            "functools.partial(%s, *%s, **%s)" % (func_string, args_string, keywords_string),
            func_imports | args_imports | keywords_imports | {"import functools"}
        )


class IteratorSerializer(BaseSerializer):
    def serialize(self):
        # Consume iterators into tuples, then serialize that
        return serializer_factory(tuple(self.value)).serialize()


class LazyObjectSerializer(BaseSerializer):
    def serialize(self):
        # The lazy object wraps a function or class
        if isinstance(self.value._setupfunc, functools.partial):
            return serializer_factory(self.value._setupfunc).serialize()
        return serializer_factory(self.value._setupfunc).serialize()


class ListSerializer(BaseSequenceSerializer):
    def _format(self):
        return "[%s]"


class ModelFieldSerializer(DeconstructableSerializer):
    def serialize(self):
        attr_name, path, args, kwargs = self.value.deconstruct()
        return self.serialize_deconstructed(path, args, kwargs)


class ModelManagerSerializer(DeconstructableSerializer):
    def serialize(self):
        as_manager, manager_path, qs_path, args, kwargs = self.value.deconstruct()
        if as_manager:
            name, imports = self._serialize_path(qs_path)
            return "%s.as_manager()" % name, imports
        else:
            return self.serialize_deconstructed(manager_path, args, kwargs)


class OperationSerializer(BaseSerializer):
    def serialize(self):
        from django.db.migrations.writer import OperationWriter
        string, imports = OperationWriter(self.value, indentation=0).serialize()
        # Nested operation, so snip off the indentation
        return string.strip(), imports


class PathLikeSerializer(BaseSerializer):
    def serialize(self):
        return repr(str(self.value)), set()


class RegexSerializer(BaseSerializer):
    def serialize(self):
        regex_pattern, pattern_imports = serializer_factory(self.value.pattern).serialize()
        # Turn off default implicit flags (e.g. re.U) because regexes with the
        # same implicit and explicit flags aren't equal.
        flags = self.value.flags ^ re.compile('').flags
        regex_flags, flag_imports = serializer_factory(flags).serialize()
        imports = {"import re"} | pattern_imports | flag_imports
        args = [regex_pattern]
        if flags:
            args.append(regex_flags)
        return "re.compile(%s)" % ', '.join(args), imports


class SequenceSerializer(BaseSequenceSerializer):
    def _format(self):
        return "(%s)"


class SetSerializer(BaseSequenceSerializer):
    def _format(self):
        # Serialize as a set literal except when value is empty because {}
        # is a dict literal, not a set.
        if self.value:
            return "{%s}"
        else:
            return "set(%s)"


class SettingsReferenceSerializer(BaseSerializer):
    def serialize(self):
        return "settings.%s" % self.value.setting_name, {"from django.conf import settings"}


class TupleSerializer(BaseSequenceSerializer):
    def _format(self):
        # When len(value)==1, the trailing comma is needed to ensure we're
        # actually creating a tuple, rather than just using parentheses.
        return "(%s%s)" % ("%s", "," if len(self.value) == 1 else "")


class TypeSerializer(BaseSerializer):
    def serialize(self):
        special_cases = [
            (models.Model, "models.Model", []),
            (type(None), 'type(None)', []),
        ]
        for case, string, imports in special_cases:
            if case is self.value:
                return string, set(imports)
        if hasattr(self.value, "__module__"):
            module = self.value.__module__
            if module == builtins.__name__:
                return self.value.__name__, set()
            else:
                return "%s.%s" % (module, self.value.__qualname__), {"import %s" % module}


class UUIDSerializer(BaseSerializer):
    def serialize(self):
        return "uuid.%s" % repr(self.value), {"import uuid"}


class Serializer:
    _registry = {
        # Some of these are order-dependent.
        frozenset: FrozensetSerializer,
        list: ListSerializer,
        set: SetSerializer,
        tuple: TupleSerializer,
        dict: DictionarySerializer,
        models.Choices: ChoicesSerializer,
        enum.Enum: EnumSerializer,
        datetime.datetime: DatetimeDatetimeSerializer,
        (datetime.date, datetime.time, datetime.timedelta): DateTimeSerializer,
        SettingsReference: SettingsReferenceSerializer,
        float: FloatSerializer,
        (bool, int, type(None), bytes, str, range): BaseSimpleSerializer,
        decimal.Decimal: DecimalSerializer,
        (functools.partial, functools.partialmethod): FunctoolsPartialSerializer,
        (types.FunctionType, types.BuiltinFunctionType, types.MethodType): FunctionTypeSerializer,
        collections.abc.Iterable: IteratorSerializer,
        (COMPILED_REGEX_TYPE, RegexObject): RegexSerializer,
        uuid.UUID: UUIDSerializer,
    }

    @classmethod
    def register(cls, type_, serializer):
        if not issubclass(serializer, BaseSerializer):
            raise ValueError("'%s' must inherit from 'BaseSerializer'." % serializer.__name__)
        cls._registry[type_] = serializer

    @classmethod
    def unregister(cls, type_):
        cls._registry.pop(type_)


def serializer_factory(value):
    if isinstance(value, Promise):
        value = str(value)
    elif isinstance(value, LazyObject):
        # The unwrapped value is returned as the first item of the arguments
        # tuple.
        value = value.__reduce__()[1][0]

    if isinstance(value, models.Field):
        return ModelFieldSerializer(value)
    if isinstance(value, models.manager.BaseManager):
        return ModelManagerSerializer(value)
    if isinstance(value, Operation):
        return OperationSerializer(value)
    if isinstance(value, type):
        return TypeSerializer(value)
    # Check for pathlib.PurePath instances
    if hasattr(value, 'parts') and hasattr(value, 'as_posix'):
        return PathLikeSerializer(value)
    # Check if it's a builtin.type
    if type(value) in Serializer._registry:
        return Serializer._registry[type(value)](value)
    for base in type(value).__mro__:
        if base in Serializer._registry:
            return Serializer._registry[base](value)
        # Special cases for things that can be imported
        if hasattr(value, 'deconstruct'):
            return DeconstructableSerializer(value)

    raise ValueError(
        "Cannot serialize: %r\nThere are some values Django cannot serialize into "
        "migration files.\nFor more, see https://docs.djangoproject.com/en/%s/"
        "topics/migrations/#migration-serializing" % (value, get_docs_version())
    )