import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = True
ALLOWED_HOSTS = ["localhost", "coptic.dev"]
SECRET_KEY="ActuallyAnythingWeAreinDev"

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
            "level": "WARNING",
        },
    },
}
# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "sqlite3.db",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
}

SEARCH_CONFIG = {
    "MEILISEARCH_URL": 'http://127.0.0.1:7700',
    "MEILISEARCH_MASTER_KEY": 'masterKey',
    "MEILISEARCH_INDEX": "texts",
}

if "test" in sys.argv:
    DATABASES["default"]["name"] = "tessqlite3.db"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_URL = "/static/"
STATICFILES_DIRS = (os.path.join(PROJECT_DIR, "static"),)
# For the time being we are using the same value for cache ttl
# both for http cache and the cached used in the scraper.
CACHE_TTL = 60  # 60 seconds 
LOCAL_REPO_PATH =  "../../corpora" # this is for upsun
# Control whether we are lazy loading the HTML generation
# This has effects both on scraping (much faster)  and in
# production.
LAZY_HTML_GENERATION = True