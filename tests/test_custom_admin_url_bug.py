import pytest
from django.contrib import admin
from django.contrib.admin.helpers import AdminReadonlyField
from django.contrib.auth.models import User
from django.db import models
from django.forms import ModelForm
from django.test import TestCase, override_settings
from django.urls import reverse, include, path


class TestModel(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        app_label = 'test_app'


class TestModelForm(ModelForm):
    class Meta:
        model = TestModel
        fields = ['name', 'user']


class TestModelAdmin(admin.ModelAdmin):
    readonly_fields = ['user']


# Create a custom admin site
custom_admin_site = admin.AdminSite(name='custom_admin')
custom_admin_site.register(User)
custom_admin_site.register(TestModel, TestModelAdmin)


# URL patterns for testing
urlpatterns = [
    path('admin/', admin.site.urls),
    path('custom-admin/', custom_admin_site.urls),
]


@override_settings(
    ROOT_URLCONF=__name__,
    INSTALLED_APPS=[
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
    ],
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    USE_TZ=False,
)
class TestCustomAdminSiteURL(TestCase):
    def setUp(self):
        # Create test data
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.test_model = TestModel.objects.create(name='Test', user=self.user)
        
    def test_issue_reproduction(self):
        """Test that get_admin_url generates correct URL for custom admin site"""
        # Get the model admin from the custom admin site
        model_admin = custom_admin_site._registry[TestModel]
        
        # Create a form instance
        form = TestModelForm(instance=self.test_model)
        
        # Create AdminReadonlyField for the 'user' field
        readonly_field = AdminReadonlyField(
            form=form,
            field='user',
            is_first=True,
            model_admin=model_admin
        )
        
        # Get the foreign key field and related object
        user_field = TestModel._meta.get_field('user')
        
        # Call get_admin_url - this should generate URL for custom admin site
        result = readonly_field.get_admin_url(user_field.remote_field, self.user)
        
        # The bug: URL should contain 'custom-admin' but contains 'admin' instead
        # Expected URL should be '/custom-admin/auth/user/1/change/'
        # But actual URL is '/admin/auth/user/1/change/'
        assert 'custom-admin' in str(result), f"Expected custom-admin in URL, got: {result}"
