#!/usr/bin/env python
import os
import sys

# Add the Django project to the path
sys.path.insert(0, '.')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

# Create a minimal settings module
with open('test_settings.py', 'w') as f:
    f.write("""
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
INSTALLED_APPS = [
    'django.contrib.staticfiles',
]
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
        ],
    },
}]
SECRET_KEY = 'test'
""")

import django
django.setup()

from django.template import Template, Context
from django.test import RequestFactory
from django.template.context import make_context

# Test current behavior
factory = RequestFactory()
request = factory.get('/test/')
request.META['SCRIPT_NAME'] = '/myapp'

template = Template('{% load static %}{% static "css/style.css" %}')
context = make_context({'request': request}, request)
result = template.render(context)

print(f"Current result: {result}")
print(f"Expected result: /myapp/static/css/style.css")
print(f"Test passes: {result == '/myapp/static/css/style.css'}")