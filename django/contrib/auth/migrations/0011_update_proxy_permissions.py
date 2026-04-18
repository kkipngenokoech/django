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
        
        # Check for existing permissions with the target content_type to avoid duplicates
        for permission in permissions_to_update:
            existing_permission = Permission.objects.filter(
                codename=permission.codename,
                content_type=new_content_type,
            ).first()
            
            if existing_permission:
                # If a permission with the same codename and target content_type already exists,
                # delete the old one to avoid duplicate key constraint violation
                permission.delete()
            else:
                # Safe to update the content_type
                permission.content_type = new_content_type
                permission.save()


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
