"""
Django settings for coptic scriptorium project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
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
	'grappelli',
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'texts',
	'annis',
	'ingest',
	'gh_ingest',
	'api',
	'mod_wsgi.server'
)

MIDDLEWARE_CLASSES = [
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
if django.VERSION[0] < 2:
	MIDDLEWARE_CLASSES.append('django.contrib.auth.middleware.SessionAuthenticationMiddleware')
MIDDLEWARE = MIDDLEWARE_CLASSES # for django >= 1.10


# for newer django
TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [os.path.join(BASE_DIR, 'templates')],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				"django.contrib.auth.context_processors.auth",
				"django.contrib.messages.context_processors.messages"
			]
		},
	}
]

# for older django
TEMPLATE_CONTEXT_PROCESSORS = (
	"django.core.context_processors.request",
	"django.contrib.auth.context_processors.auth"
)

ROOT_URLCONF = 'coptic.urls'

WSGI_APPLICATION = 'coptic.wsgi.application'

LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'formatters': {
	    'verbose': {
	   	 'format': '%(asctime)s\t%(levelname)s\t%(module)s\t%(message)s'
	    },
	},
	'handlers': {
	    'file': {
	   	 'level': 'INFO',
	   	 'class': 'logging.FileHandler',
	   	 'filename': BASE_DIR + "/" + os.path.join("django_logger.log"),
	   	 'formatter': 'verbose',
	    },
	    'filedb': {
	   	 'level': 'INFO',
	   	 'class': 'logging.FileHandler',
	   	 'filename': BASE_DIR + "/" + os.path.join("django_db.log"),
	   	 'formatter': 'verbose',
	    },
	    'console': {
	   	 'class': 'logging.StreamHandler',
	   	 'stream': sys.stdout,
	   	 'formatter': 'verbose',
	    }
	},
	'loggers': {
	    'ingest.ingest': {
	   	 'handlers': ['console', 'file'],
	   	 'level': 'INFO',
	    },
	    'ingest.models': {
	   	 'handlers': ['console', 'file'],
	   	 'level': 'INFO',
	    },
	    'ingest.search': {
	   	 'handlers': ['console', 'file'],
	   	 'level': 'INFO',
	    },
	    'django': {
	   	 'handlers': ['console', 'file'],
	   	 'level': 'INFO',
	    },
	}
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = False

# Templates
TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

# SCRIPTORIUM-specific config
CORPUS_REPO_OWNER = "CopticScriptorium"
CORPUS_REPO_NAME  = "corpora"
