import datetime
import decimal
import json
from collections import defaultdict

from django.core.exceptions import FieldDoesNotExist
from django.db import models, router
from django.db.models.constants import LOOKUP_SEP
from django.db.models.deletion import Collector
from django.forms.utils import pretty_name
from django.urls import NoReverseMatch, reverse
from django.utils import formats, timezone
from django.utils.html import format_html
from django.utils.regex_helper import _lazy_re_compile
from django.utils.text import capfirst
from django.utils.translation import ngettext, override as translation_override

QUOTE_MAP = {i: '_%02X' % i for i in b'":/_#?;@&=+$,"[]<>%\n\\'}
UNQUOTE_MAP = {v: chr(k) for k, v in QUOTE_MAP.items()}
UNQUOTE_RE = _lazy_re_compile('_(?:%s)' % '|'.join([x[1:] for x in UNQUOTE_MAP]))


class FieldIsAForeignKeyColumnName(Exception):
    """A field is a foreign key attname, i.e. <FK>_id."""
    pass


def lookup_needs_distinct(opts, lookup_path):
    """
    Return True if 'distinct()' should be used to query the given lookup path.
    """
    lookup_fields = lookup_path.split(LOOKUP_SEP)
    # Go through the fields (following all relations) and look for an m2m.
    for field_name in lookup_fields:
        if field_name == 'pk':
            field_name = opts.pk.name
        try:
            field = opts.get_field(field_name)
        except FieldDoesNotExist:
            # Ignore query lookups.
            continue
        else:
            if hasattr(field, 'get_path_info'):
                # This field is a relation; update opts to follow the relation.
                path_info = field.get_path_info()
                opts = path_info[-1].to_opts
                if any(path.m2m for path in path_info):
                    # This field is a m2m relation so distinct must be called.
                    return True
    return False


def prepare_lookup_value(key, value):
    """
    Return a lookup value prepared to be used in queryset filtering.
    """
    # if key ends with __in, split parameter into separate values
    if key.endswith('__in'):
        value = value.split(',')
    # if key ends with __isnull, special case '' and the string literals 'false' and '0'
    elif key.endswith('__isnull'):
        value = value.lower() not in ('', 'false', '0')
    return value


def quote(s):
    """
    Ensure that primary key values do not confuse the admin URLs by escaping
    any '/', '_' and ':' and similarly problematic characters.
    Similar to urllib.parse.quote(), except that the quoting is slightly
    different so that it doesn't get automatically unquoted by the Web browser.
    """
    return s.translate(QUOTE_MAP) if isinstance(s, str) else s


def unquote(s):
    """Undo the effects of quote()."""
    return UNQUOTE_RE.sub(lambda m: UNQUOTE_MAP[m.group(0)], s)


def flatten(fields):
    """
    Return a list which is a single level of flattening of the original list.
    """
    flat = []
    for field in fields:
        if isinstance(field, (list, tuple)):
            flat.extend(field)
        else:
            flat.append(field)
    return flat


def flatten_fieldsets(fieldsets):
    """Return a list of field names from an admin fieldsets structure."""
    field_names = []
    for name, opts in fieldsets:
        field_names.extend(
            flatten(opts['fields'])
        )
    return field_names


def get_deleted_objects(objs, request, admin_site):
    """
    Find all objects related to ``objs`` that should also be deleted. ``objs``
    must be a homogeneous iterable of objects (e.g. a QuerySet).

    Return a nested list of strings suitable for display in the
    template with the ``unordered_list`` filter.
    """
    try:
        obj = objs[0]
    except IndexError:
        return [], {}, set(), []
    else:
        using = router.db_for_write(obj._meta.model)
    collector = Collector(using=using)
    collector.collect(objs)
    perms_needed = set()

    def format_callback(obj):
        model = obj.__class__
        has_admin = model in admin_site._registry
        opts = obj._meta

        no_edit_link = '%s: %s' % (capfirst(opts.verbose_name), obj)

        if has_admin:
            if not admin_site._registry[model].has_delete_permission(request, obj):
                perms_needed.add(opts.verbose_name)
            try:
                admin_url = reverse('%s:%s_%s_change' %
                                    (admin_site.name,
                                     opts.app_label,
                                     opts.model_name),
                                    None, (quote(obj.pk),))
            except NoReverseMatch:
                # Change url doesn't exist -- don't display link to edit
                return no_edit_link

            # Display a link to the admin page.
            return format_html('{}: <a href="{}">{}</a>',
                               capfirst(opts.verbose_name),
                               admin_url,
                               obj)
        else:
            # Don't display link to edit, because it either has no
            # admin or is edited inline.
            return no_edit_link

    to_delete = collector.nested(format_callback)

    protected = [format_callback(obj) for obj in collector.protected]
    model_count = {model._meta.verbose_name_plural: len(objs) for model, objs in collector.model_objs.items()}

    return to_delete, model_count, perms_needed, protected


def model_format_dict(obj):
    """
    Return a `dict` with keys 'verbose_name' and 'verbose_name_plural',
    typically for use with string formatting.

    `obj` may be a `Model` instance, `Model` subclass, or `QuerySet` instance.
    """
    if isinstance(obj, (models.Model, models.base.ModelBase)):
        opts = obj._meta
    elif isinstance(obj, models.query.QuerySet):
        opts = obj.model._meta
    else:
        opts = obj
    return {
        'verbose_name': opts.verbose_name,
        'verbose_name_plural': opts.verbose_name_plural,
    }


def model_ngettext(obj, n=None):
    """
    Return the appropriate `verbose_name` or `verbose_name_plural` value for
    `obj` depending on the count `n`.

    `obj` may be a `Model` instance, `Model` subclass, or `QuerySet` instance.
    If `obj` is a `QuerySet` instance, `n` is optional and the length of the
    `QuerySet` is used.
    """
    if isinstance(obj, models.query.QuerySet):
        if n is None:
            n = obj.count()
        obj = obj.model
    d = model_format_dict(obj)
    singular, plural = d["verbose_name"], d["verbose_name_plural"]
    return ngettext(singular, plural, n or 0)


def lookup_field(name, obj, model_admin=None):
    opts = obj._meta
    try:
        f = opts.get_field(name)
    except FieldDoesNotExist:
        # For non-field values, the value is either a method, property or
        # returned via a callable.
        if callable(name):
            attr = name
            value = attr(obj)
        elif hasattr(model_admin, name) and name != '__str__':
            attr = getattr(model_admin, name)
            value = attr(obj) if callable(attr) else attr
        elif hasattr(obj, name) and name != '__str__':
            attr = getattr(obj, name)
            value = attr() if callable(attr) else attr
        else:
            raise AttributeError
        # Strip HTML tags in the resulting text, except if the attribute is
        # marked as allowing them.
        if isinstance(value, str) and not getattr(attr, 'allow_tags', False):
            value = format_html('{}', value)
        return f, attr, value
    else:
        # Fields need to be handled differently than non-fields.
        if f.many_to_many or f.one_to_many:
            raise FieldIsAForeignKeyColumnName
        # Non-relation fields.
        if f.flatchoices:
            value = getattr(obj, f.attname)
            return f, f.verbose_name, dict(f.flatchoices).get(value, value)
        value = getattr(obj, f.attname)
        # Foreign keys.
        if f.many_to_one:
            if value is None:
                return f, f.verbose_name, None
            else:
                rel_obj = f.related_model.objects.get(pk=value)
                return f, f.verbose_name, rel_obj
        # Reverse foreign keys.
        elif f.one_to_one:
            try:
                rel_obj = getattr(obj, f.name)
            except AttributeError:
                return f, f.verbose_name, None
            else:
                return f, f.verbose_name, rel_obj
        # Non-relations.
        else:
            return f, f.verbose_name, value


def _boolean_icon(field_val):
    icon_url = 'admin/img/icon-%s.svg' % {True: 'yes', False: 'no', None: 'unknown'}[field_val]
    return format_html('<img src="{}" alt="{}">', icon_url, field_val)


def display_for_field(value, field, empty_value_display):
    from django.contrib.admin.templatetags.admin_list import _boolean_icon
    from django.contrib.postgres.fields import JSONField

    if getattr(field, 'flatchoices', None):
        return dict(field.flatchoices).get(value, empty_value_display)
    # BooleanField needs special-case null-handling, so it comes before the
    # general null test.
    elif isinstance(field, models.BooleanField):
        return _boolean_icon(value)
    elif value is None:
        return empty_value_display
    elif isinstance(field, models.DateTimeField):
        return formats.localize(timezone.template_localtime(value))
    elif isinstance(field, (models.DateField, models.TimeField)):
        return formats.localize(value)
    elif isinstance(field, models.DecimalField):
        return formats.number_format(value)
    elif isinstance(field, (models.IntegerField, models.FloatField)):
        return formats.number_format(value)
    elif isinstance(field, models.FileField) and value:
        return format_html('<a href="{}">{}</a>', value.url, value)
    elif isinstance(field, JSONField):
        try:
            return json.dumps(value, ensure_ascii=False, cls=field.encoder)
        except (TypeError, ValueError):
            return str(value)
    else:
        return str(value)


def display_for_value(value, empty_value_display, boolean=False):
    from django.contrib.admin.templatetags.admin_list import _boolean_icon

    if boolean:
        return _boolean_icon(value)
    elif value is None:
        return empty_value_display
    elif isinstance(value, bool):
        return str(value)
    elif isinstance(value, datetime.datetime):
        return formats.localize(timezone.template_localtime(value))
    elif isinstance(value, (datetime.date, datetime.time)):
        return formats.localize(value)
    elif isinstance(value, (int, decimal.Decimal, float)):
        return formats.number_format(value)
    elif isinstance(value, (list, tuple)):
        return ', '.join(str(v) for v in value)
    else:
        return str(value)


class NotRelationField(Exception):
    pass


def get_model_from_relation(field):
    if hasattr(field, 'get_path_info'):
        return field.get_path_info()[-1].to_opts.model
    else:
        raise NotRelationField


def reverse_field_path(model, path):
    """ Create a reversed field path.

    E.g. Given (Order, "user__groups"),
    return (Group, "user__order_set").
    """
    # path can be written as "field1__field2__field3__..."
    # reverse_path should be "field3__field2__field1__..."
    path = path.split(LOOKUP_SEP)
    reversed_path = []
    parent = model._meta
    for piece in path:
        field = parent.get_field(piece)
        # skip trailing data lookups
        if field.is_relation:
            # add to the path, and update the parent
            reversed_path.insert(0, field.remote_field.get_accessor_name())
            parent = field.remote_field.model._meta
        else:
            break
    return (parent.model, LOOKUP_SEP.join(reversed_path))


def get_fields_from_path(model, path):
    """ Return list of Fields given path relative to model.

    e.g. (ModelX, "user__groups__name") -> [
        <django.db.models.fields.related.ForeignKey object at 0x...>,
        <django.db.models.fields.related.ManyToManyField object at 0x...>,
        <django.db.models.fields.CharField object at 0x...>,
    ]
    """
    pieces = path.split(LOOKUP_SEP)
    fields = []
    for piece in pieces:
        if fields:
            parent = get_model_from_relation(fields[-1])
        else:
            parent = model
        fields.append(parent._meta.get_field(piece))
    return fields


def construct_change_message(form, formsets, add):
    """
    Construct a JSON structure describing changes from a changed object.
    Translations are deactivated so that strings are stored untranslated.
    Translation happens later on LogEntry access.
    """
    def get_field_name(field):
        return field.verbose_name

    change_message = []
    if add:
        change_message.append({'added': {}})
    elif form.changed_data:
        changed_fields = []
        for name in form.changed_data:
            try:
                field = form.fields[name]
                changed_fields.append(get_field_name(field))
            except KeyError:
                # Handle edge case where field is not in form.fields
                changed_fields.append(name)
        if changed_fields:
            change_message.append({'changed': {'fields': changed_fields}})

    if formsets:
        with translation_override(None):
            for formset in formsets:
                for added_object in formset.new_objects:
                    change_message.append({
                        'added': {
                            'name': str(added_object._meta.verbose_name),
                            'object': str(added_object),
                        }
                    })
                for changed_object, changed_fields in formset.changed_objects:
                    change_message.append({
                        'changed': {
                            'name': str(changed_object._meta.verbose_name),
                            'object': str(changed_object),
                            'fields': changed_fields,
                        }
                    })
                for deleted_object in formset.deleted_objects:
                    change_message.append({
                        'deleted': {
                            'name': str(deleted_object._meta.verbose_name),
                            'object': str(deleted_object),
                        }
                    })
    return change_message