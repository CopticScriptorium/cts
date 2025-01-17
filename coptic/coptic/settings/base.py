"""
Django settings for coptic scriptorium project.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from collections import OrderedDict
import os

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


CORPUS_MAP = {
"acts.pilate":{"title":"Acts of Pilate - Gospel of Nicodemus","urn":"urn:cts:copticLit:misc.acts_pilate.lacau_ed"},
"apophthegmata.patrum":{"title":"Apophthegmata Patrum","urn":"urn:cts:copticLit:ap", "slug":"ap"},
"besa.letters":{"title":"Besa Letters","urn":"urn:cts:copticLit:besa", "slug":"besa_letters"},
"bohairic.1corinthians":{"title":"Bohairic 1 Corinthians","urn":"urn:cts:copticLit:nt.1cor.bohairic_ed"},
"bohairic.habakkuk":{"title":"Bohairic Habakkuk","urn":"urn:cts:copticLit:ot.hab.bohairic_ed"},
"bohairic.life.isaac":{"title":"Bohairic Life of Isaac","urn":"urn:cts:copticLit:lives.boh_isaac"},
"bohairic.mark":{"title":"Bohairic Mark","urn":"urn:cts:copticLit:nt.mark.bohairic_ed"},
"bohairic.nt":{"title":"Bohairic New Testament","urn":"urn:cts:copticLit:nt.bohairic"},
"bohairic.ot":{"title":"Bohairic Old Testament","urn":"urn:cts:copticLit:ot.bohairic_ed"},
"doc.papyri":{"title":"Documentary Papyri","urn":"urn:cts:copticDoc:papyri_info", "slug":"papyri"},
"book.bartholomew":{"title":"Book of Bartholomew","urn":"urn:cts:copticLit:misc.blbartholomew"},
"dormition.john":{"title":"Dormition of John","urn":"urn:cts:copticLit:misc.dormition_john"},
"helias":{"title":"Helias","urn":"urn:cts:copticLit:helias"},
"johannes.canons":{"title":"Apa Johannes Canons","urn":"urn:cts:copticLit:johannes.canons", "slug":"johannes"},
"john.constantinople":{"title":"John of Constantinople Discourse","urn":"urn:cts:copticLit:johnconst.penitence"},
"lament.mary":{"title":"Lament of Mary","urn":"urn:cts:copticLit:misc.lament_mary"},
"life.aphou":{"title":"Life of Aphou","urn":"urn:cts:copticLit:lives.aphou"},
"life.cyrus":{"title":"Life of Cyrus","urn":"urn:cts:copticLit:lives.cyrus"},
"life.eustathius.theopiste":{"title":"The History of Eustathius and Theopiste","urn":"urn:cts:copticLit:lives.eustathius"},
"life.john.kalybites":{"title":"Life of John the Kalybites","urn":"urn:cts:copticLit:lives.john_kalybites"},
"life.longinus.lucius":{"title":"Life of Longinus and Lucius","urn":"urn:cts:copticLit:lives.longinus_lucius"},
"life.onnophrius":{"title":"Life of Onnophrius","urn":"urn:cts:copticLit:lives.onnophrius"},
"life.paul.tamma":{"title":"Life of Paul of Tamma","urn":"urn:cts:copticLit:lives.paul_tamma"},
"life.phib":{"title":"Life of Phib","urn":"urn:cts:copticLit:lives.phib"},
"life.pisentius":{"title":"Life of Pisentius","urn":"urn:cts:copticLit:lives.pisentius"},
"magical.papyri":{"title":"Magical Papyri","urn":"urn:cts:copticMag:kyprianos"},
"martyrdom.victor":{"title":"Martyrdom of Victor the General","urn":"urn:cts:copticLit:martyrdoms.victor", "slug":"victor"},
"mercurius":{"title":"Mercurius Encomium, Martyrdom and Miracles","urn":"urn:cts:copticLit:mercurius"},
"mysteries.john":{"title":"Mysteries of John the Evangelist","urn":"urn:cts:copticLit:misc.mysteries_john"},
"pachomius.instructions":{"title":"Instructions of Apa Pachomius","urn":"urn:cts:copticLit:pachomius.instructions"},
"pistis.sophia":{"title":"Pistis Sophia","urn":"urn:cts:copticLit:pistissophia"},
"proclus.homilies":{"title":"Proclus Homilies","urn":"urn:cts:copticLit:proclus"},
"pseudo.athanasius.discourses":{"title":"Pseudo-Athanasius Discourses","urn":"urn:cts:copticLit:psathanasius.discourses"},
"pseudo.basil":{"title":"Pseudo-Basil of Caesarea Discourse","urn":"urn:cts:copticLit:psbasilcaesarea"},
"pseudo.celestinus":{"title":"Encomium on Victor","urn":"urn:cts:copticLit:pscelestinus.encomium"},
"pseudo.chrysostom":{"title":"Pseudo-Chrysostom","urn":"urn:cts:copticLit:pschrysostom"},
"pseudo.ephrem":{"title":"Pseudo-Ephrem Writings","urn":"urn:cts:copticLit:psephrem"},
"pseudo.flavianus":{"title":"Encomium on Demetrius Archbishop of Alexandria","urn":"urn:cts:copticLit:psflavianus.encomium"},
"pseudo.theophilus":{"title":"Pseudo-Theophilus","urn":"urn:cts:copticLit:pstheophilus", "slug":"pseudotheophilus"},
"pseudo.timothy":{"title":"Pseudo-Timothy of Alexandria Discourses","urn":"urn:cts:copticLit:pstimothy"},
"sahidic.ot":{"title":"Old Testament","urn":"urn:cts:copticLit:ot", "slug":"old-testament"},
"sahidic.ruth":{"title":"Ruth","urn":"urn:cts:copticLit:ot.ruth.coptot"},
"sahidica.nt":{"title":"New Testament","urn":"urn:cts:copticLit:nt.sahidica_ed", "slug":"new-testament"},
"sahidica.1corinthians":{"title":"1 Corinthians","urn":"urn:cts:copticLit:nt.1cor.sahidica_ed", "slug":"1st_corinthians"},
"sahidica.mark":{"title":"Gospel of Mark","urn":"urn:cts:copticLit:nt.mark.sahidica_ed", "slug":"gospel_of_mark"},
"shenoute.a22":{"title":"Acephalous Work 22","urn":"urn:cts:copticLit:shenoute.a22", "slug":"acephalous_work_22"},
"shenoute.abraham":{"title":"Abraham Our Father","urn":"urn:cts:copticLit:shenoute.abraham", "slug":"abraham_our_father"},
"shenoute.considering":{"title":"I Have Been Considering","urn":"urn:cts:copticLit:shenoute.considering.amelineau"},
"shenoute.crushed":{"title":"My Heart Is Crushed","urn":"urn:cts:copticLit:shenoute.crushed.amelineau"},
"shenoute.dirt":{"title":"Some Kinds of People Sift Dirt","urn":"urn:cts:copticLit:shenoute.dirt", "slug":"shenoutedirt"},
"shenoute.eagerness":{"title":"I See Your Eagerness","urn":"urn:cts:copticLit:shenoute.eagerness", "slug":"eagernesss"},
"shenoute.errs":{"title":"If Everyone Errs","urn":"urn:cts:copticLit:shenoute.errs.amelineau"},
"shenoute.fox":{"title":"Not Because a Fox Barks","urn":"urn:cts:copticLit:shenoute.fox", "slug":"not_because_a_fox_barks"},
"shenoute.house":{"title":"This Great House","urn":"urn:cts:copticLit:shenoute.house.amelineau"},
"shenoute.listen":{"title":"So Listen","urn":"urn:cts:copticLit:shenoute.listen.amelineau"},
"shenoute.place":{"title":"So Concerning the Little Place","urn":"urn:cts:copticLit:shenoute.place.amelineau"},
"shenoute.seeks":{"title":"Whoever Seeks God Will Find","urn":"urn:cts:copticLit:shenoute.seeks"},
"shenoute.those":{"title":"God Says Through Those Who Are His","urn":"urn:cts:copticLit:shenoute.those"},
"shenoute.true":{"title":"God Who Alone Is True","urn":"urn:cts:copticLit:shenoute.true.amelineau"},
"shenoute.uncertain.xr":{"title":"Uncertain Canons in MONB.XR","urn":"urn:cts:copticLit:shenoute.uncertain_xr.amelineau"},
"shenoute.unknown5_1":{"title":"Unknown Work 5-1","urn":"urn:cts:copticLit:shenoute.unknown5_1"},
"shenoute.night":{"title":"In the Night","urn":"urn:cts:copticLit:shenoute.night"},
"shenoute.prince":{"title":"Because of You Too O Prince of Evil","urn":"urn:cts:copticLit:shenoute.prince"},
"shenoute.thundered":{"title":"The Lord Thundered","urn":"urn:cts:copticLit:shenoute.thundered.amelineau"},
"shenoute.witness":{"title":"Who but God is the Witness","urn":"urn:cts:copticLit:shenoute.witness.amelineau"},
"theodosius.alexandria":{"title":"Encomium on Michael the Archangel","urn":"urn:cts:copticLit:theodosiusalex.michael"}
}

METAS = {
    "corpus": {"name":"corpus", "order":1, "splitter":""}, 
    "author": {"name":"author", "order":2, "splitter":""},
    "people": {"name":"people", "order":3, "splitter":";"}, 
    "places": {"name":"places", "order":4, "splitter":";"},
    "ms_name": {"name":"msName", "order":5, "splitter":""},
    "annotation": {"name":"annotation", "order":6, "splitter":","},
    "translation": {"name":"translation", "order":7, "splitter":","},
    "arabic_translation": {"name":"arabic_translation", "order":8, "splitter":","},
}

HTML_VISUALISATION_FORMATS = OrderedDict([
            ("norm", dict(slug="norm", button_title="normalized", title="Normalized Text")),
            ("analytic", dict(slug="analytic", button_title="analytic", title="Analytic Visualization")),
            ("dipl", dict(slug="dipl", button_title="diplomatic", title="Diplomatic Edition")),
            ("sahidica", dict(slug="sahidica", button_title="chapter", title="Sahidica Chapter View")),
            ("versified", dict(slug="verses", button_title="versified", title="Versified Text")),
])

HTML_CONFIGS = { 
"dipl":"""pb_xml_id	table:title; style="pb"	value
pb_xml_id	tr
cb_n	td; style="cb"
lb_n	div:line; style="copt_line"	value
hi_rend	hi_rend:rend	value
tok	span	value
orig_word	a	" "
""",
"analytic" : """chapter_n	div:chapter; style="chapter"	value
translation div:trans; style="translation"	value
verse_n	div:verse; style="verse"	value
identity	div; style="named"
entity	div:entity_type; style="entity"	value
identity	div; style="identity"	"<a href='https://en.wikipedia.org/wiki/%%value%%' title='%%value%%' class='wikify' target='__new'></a>"
norm_group	i; style="copt_word"
norm	ruby; style="norm"
lemma	NULL	"<a href='%%value%%' target='_new'>"
norm	NULL	"%%value%%"
pos	NULL	"</a>"
pos	rt:pos; style="pos"	value
pb_xml_id	q:page; style="page"	value
""",
"verses" : """chapter_n	div:chapter; style="chapter"	value
orig_group	span; style="word"
norm	span; style="norm"
lemma	NULL	"<a href='%%value%%' target='_new'>"
norm	NULL	"%%value%%"
pos	NULL	"</a>"
translation t:title; style="translation"	value
verse_n	div:verse; style="verse"	value
pb_xml_id	q:page; style="page"	value""",
"sahidica" : """orig_group	span; style="word"
norm	span; style="norm"
lemma	NULL	"<a href='%%value%%' target='_new'>"
norm	NULL	"%%value%%"
pos	NULL	"</a>"
translation t:title; style="translation"	value
verse_n	div:verse; style="verse"	value
"""
}
