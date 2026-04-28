
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
