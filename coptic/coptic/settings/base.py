"""
Django settings for coptic scriptorium project.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import django
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# Application definition
INSTALLED_APPS = (
    "grappelli",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "texts",
    "gh_ingest",
    "mod_wsgi.server",
)

MIDDLEWARE = [
   # Security middleware should come early in the stack
    'django.middleware.security.SecurityMiddleware',  
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Cache middleware should typically be last
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
]

# for newer django
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]
        },
    }
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ROOT_URLCONF = "coptic.urls"

WSGI_APPLICATION = "coptic.wsgi.application"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(asctime)s\t%(levelname)s\t%(module)s\t%(message)s"},
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR + "/" + os.path.join("django_logger.log"),
            "formatter": "verbose",
        },
        "filedb": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR + "/" + os.path.join("django_db.log"),
            "formatter": "verbose",
        },
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
    },
}
# Cache configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/tmp/django_cache",
    }
}

CACHE_TTL = 60 * 60 * 24 * 7  # 1 week

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = False

# Templates
TEMPLATE_DIRS = [os.path.join(BASE_DIR, "templates")]

# SCRIPTORIUM-specific config
CORPUS_REPO_OWNER = "CopticScriptorium"
CORPUS_REPO_NAME = "corpora"
GITHUB_API_BASE_URL = "https://api.github.com"

DEPRECATED_URNS = {
    "urn:cts:copticLit:shenoute.a22.monbyb_307_320": "urn:cts:copticLit:shenoute.a22.monbyb:801-825",
    "urn:cts:copticLit:shenoute.a22.monbzc_301_308": "urn:cts:copticLit:shenoute.a22.monbzc:1001-1006",
    "urn:cts:copticLit:shenoute.a22.monbya_421_428": "urn:cts:copticLit:shenoute.a22.monbya:1251-1258",
    "urn:cts:copticLit:shenoute.a22.monbya_517_518": "urn:cts:copticLit:shenoute.a22.monbya:1451-1453",
    "urn:cts:copticLit:shenoute.abraham.monbya_518_520": "urn:cts:copticLit:shenoute.abraham.monbya:1-4",
    "urn:cts:copticLit:shenoute.abraham.monbya_525_530": "urn:cts:copticLit:shenoute.abraham.monbya:10-18",
    "urn:cts:copticLit:shenoute.abraham.monbzh_frg1_a_d": "urn:cts:copticLit:shenoute.abraham.monbzh:18-21",
    "urn:cts:copticLit:shenoute.abraham.monbya_535_540": "urn:cts:copticLit:shenoute.abraham.monbya:21-27",
    "urn:cts:copticLit:shenoute.abraham.monbxl_93_94": "urn:cts:copticLit:shenoute.abraham.monbxl:23-24",
    "urn:cts:copticLit:shenoute.abraham.monbya_547_550": "urn:cts:copticLit:shenoute.abraham.monbya:37-42",
    "urn:cts:copticLit:shenoute.abraham.monbya_551_554": "urn:cts:copticLit:shenoute.abraham.monbya:42-47",
}
