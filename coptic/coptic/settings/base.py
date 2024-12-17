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

KNOWN_SLUGS = {
    "apophthegmata.patrum": "ap",
    "besa.letters": "besa_letters",
    "doc.papyri": "papyri",
    "johannes.canons": "johannes",
    "martyrdom.victor": "victor",
    "pseudo.theophilus": "pseudotheophilus",
    "sahidic.ot": "old-testament",
    "sahidica.1corinthians": "1st_corinthians",
    "sahidica.mark": "gospel_of_mark",
    "sahidica.nt": "new-testament",
    "shenoute.a22": "acephalous_work_22",
    "shenoute.abraham": "abraham_our_father",
    "shenoute.dirt": "shenoutedirt",
    "shenoute.eagerness": "eagernesss",
    "shenoute.fox": "not_because_a_fox_barks",
}

HTML_CONFIGS = { 
"dipl":"""pb_xml_id	table:title; style="pb"	value
pb_xml_id	tr
cb_n	td; style="cb"
lb_n	div:line; style="copt_line"	value
hi_rend	hi_rend:rend	value
tok	span	value
orig_word	a	" "
""",
"analytic":"""chapter_n	div:chapter; style="chapter"	value
translation div:trans; style="translation"	value
verse_n	div:verse; style="verse"	value
identity	div; style="named"
entity	div:entity_type; style="entity"	value
identity	div; style="identity"	"<a href='https://en.wikipedia.org/wiki/%%value%%' title='%%value%%' class='wikify' target='__new'></a>"
norm_group	i; style="copt_word"
norm	ruby; style="norm"
lemma	NULL	"<a href='https://coptic-dictionary.org/results.cgi?quick_search=%%value%%' target='_new'>"
norm	NULL	"%%value%%"
pos	NULL	"</a>"
pos	rt:pos; style="pos"	value
pb_xml_id	q:page; style="page"	value""",
"sahidic":"""
chapter_n	div:chapter; style="chapter"	value
orig_group	span; style="word"
norm	span; style="norm"
lemma	NULL	"<a href='https://coptic-dictionary.org/results.cgi?quick_search=%%value%%' target='_new'>"
norm	NULL	"%%value%%"
pos	NULL	"</a>"
translation t:title; style="translation"	value
verse_n	div:verse; style="verse"	value
pb_xml_id	q:page; style="page"	value""" }