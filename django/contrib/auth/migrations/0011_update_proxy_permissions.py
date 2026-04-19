from django.db import migrations
from django.db.models import Q


def update_proxy_model_permissions(apps, schema_editor, reverse=False):
    """
    Update the content_type of proxy model permissions to use the ContentType
    of the proxy model.
    """
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    for Model in apps.get_models():
        opts = Model._meta
        if not opts.proxy:
            continue
        proxy_default_permissions_codenames = [
            '%s_%s' % (action, opts.model_name)
            for action in opts.default_permissions
        ]
        permissions_query = Q(codename__in=proxy_default_permissions_codenames)
        for codename, name in opts.permissions:
            permissions_query = permissions_query | Q(codename=codename, name=name)
        concrete_content_type = ContentType.objects.get_for_model(Model, for_concrete_model=True)
        proxy_content_type = ContentType.objects.get_for_model(Model, for_concrete_model=False)
        old_content_type = proxy_content_type if reverse else concrete_content_type
        new_content_type = concrete_content_type if reverse else proxy_content_type
        
        # Get permissions that need to be updated
        permissions_to_update = Permission.objects.filter(
            permissions_query,
            content_type=old_content_type,
        )
        
        # Check for existing permissions with the target content type that would cause conflicts
        existing_permissions = Permission.objects.filter(
            permissions_query,
            content_type=new_content_type,
        )
        
        if existing_permissions.exists():
            # Get the codenames of existing permissions to avoid conflicts
            existing_codenames = set(existing_permissions.values_list('codename', flat=True))
            
            # Filter out permissions that would cause conflicts
            permissions_to_update = permissions_to_update.exclude(
                codename__in=existing_codenames
            )
            
            # Delete the conflicting permissions from the old content type
            # since we already have them for the new content type
            Permission.objects.filter(
                permissions_query,
                content_type=old_content_type,
                codename__in=existing_codenames,
            ).delete()
        
        # Update the remaining permissions
        permissions_to_update.update(content_type=new_content_type)


def revert_proxy_model_permissions(apps, schema_editor):
    """
    Update the content_type of proxy model permissions to use the ContentType
    of the concrete model.
    """
    update_proxy_model_permissions(apps, schema_editor, reverse=True)


class Migration(migrations.Migration):
    dependencies = [
        ('auth', '0010_alter_group_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]
    operations = [
        migrations.RunPython(update_proxy_model_permissions, revert_proxy_model_permissions),
    ]