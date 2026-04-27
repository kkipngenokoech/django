import tempfile
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django_tests_secret_key'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'TEST': {
            'NAME': 'test_default.sqlite3'
        },
        'OPTIONS': {
            'timeout': 30,
            'init_command': "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA temp_store=memory; PRAGMA mmap_size=268435456;",
        },
    },
    'other': {
        'ENGINE': 'django.db.backends.sqlite3',
        'TEST': {
            'NAME': 'test_other.sqlite3'
        },
        'OPTIONS': {
            'timeout': 30,
            'init_command': "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA temp_store=memory; PRAGMA mmap_size=268435456;",
        },
    }
}

USE_TZ = False

SECRET_KEY = "django_tests_secret_key"

USE_I18N = True

USE_L10N = True

STATIC_URL = '/static/'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'