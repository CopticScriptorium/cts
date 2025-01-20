import os
import sys
from django.core.exceptions import DisallowedHost
from django.utils.http import is_same_domain

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Fetch the allowed hosts from the environment variable
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() in ("true", "1")
TEMPLATE_DEBUG = DEBUG

#SETUP Logging.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(asctime)s\t%(levelname)s\t%(module)s\t%(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}
# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db/sqlite3.db",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/tmp/django_cache",
    }
}


SEARCH_CONFIG = {
    "MEILI_HTTP_ADDR":  os.getenv('MEILI_HTTP_ADDR','http://localhost:7700/'),
    "MEILI_MASTER_KEY": os.getenv('MEILLI_MASTER_KEY', 'masterKey'),
    "MEILI_COPTIC_INDEX": "texts",
    "DISABLE": False,
}

# Use test database if running tests
if "test" in sys.argv:
    DATABASES["default"]["NAME"] = "db/test_sqlite3.db"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_URL = "/static/"
STATICFILES_DIRS = (os.path.join(PROJECT_DIR, "static"),)
LOCAL_REPO_PATH =  "/app/corpora" # this is for upsun

CACHE_TTL = 60 * 60 * 24 * 7  # 1 week
# Control whether we are lazy loading the HTML generation
LAZY_HTML_GENERATION = True
