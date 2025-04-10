# Introduction

This project allows to have a web interface to navigate coptic corpora created through the ANNIS system. It is a visualisation system only.

It is a Django application which has an admin interface at /admin

The import procedure stores imported data in an SQLITE database, optionally indexing it in Meilisearch.

It imports the exported data, present in the https://github.com/CopticScriptorium/corpora/ **repository**.

The configuration of the import is done in code within the [](coptic/settings/base.py) file that namely contains:
* **DEPRECATED_URNS** - a list of deprecated URNS
* **CORPUS_MAP**  - a dictionary of specific configuration for each corpus, such as its `title`, `urn` and `slug` (when it is different from the one created by default)
* **METAS** - that control how metadata found in the SGML documents will be processed and presented
* **HTML_VISUALISATION_FORMATS** - available visualisation formats and their displayable names

* Each directory in the **repository** represents a corpus. For example https://github.com/CopticScriptorium/corpora/tree/master/acts-pilate contains the export of "Acts of Pilate - Gospel of Nicodemu".
* The directory of type: `{name}_ANNIS` contain some important configuration files. Most importantly `resolver_vis_map.annis` (in this example https://github.com/CopticScriptorium/corpora/blob/master/acts-pilate/acts.pilate_ANNIS/resolver_vis_map.annis) that lists the visualisations associated with each text in the corpus.
* The directory ExtData (in this example https://github.com/CopticScriptorium/corpora/tree/master/acts-pilate/acts.pilate_ANNIS/ExtData) contains for each visualisation the configuration of the visualisation which is made of parsing rules for the SGML content for example https://github.com/CopticScriptorium/corpora/blob/master/acts-pilate/acts.pilate_ANNIS/ExtData/analytic.config for the `analytic` visualisation a directive such as `chapter_n	div:chapter; style="chapter"	value` means creating a wrapper html elevent of type div. The directory also contains an associated css file here, https://github.com/CopticScriptorium/corpora/blob/master/acts-pilate/acts.pilate_ANNIS/ExtData/analytic.css.
* The SGML content is present in a directory of type `{name}_ANNIS` which will contain the actual content for example https://github.com/CopticScriptorium/corpora/blob/master/acts-pilate/acts.pilate_TT/pilate.1643.27-28.tt
* Each document contains a `<meta>` tag with metadata on each text which allows to navigate the corpora after imported.
* Further documentation on the visualisation generation is found in [](gh_ingest/docs/README_htmlvis.md)

## CAVEAT

* Corpora have multiple ways to be addressed that are slightly different and can lead to some confusion through the implementation: the top-level directory  may be `acts-pilate`. the "ANNIS" directories `acts.pilate` the slug in the database `actspilate` and the urn `acts_pilate`.
* The same goes for visualisations that may have different technical names in different contexts. (`verses`, `versified` ). Critically the implementation actually uses the button_title to select the visualisation format. See [button_title](https://github.com/CopticScriptorium/cts/blame/a1b616cd527002353cd7185807921208667dda2f/coptic/gh_ingest/scraper.py#L251C91-L251C103) which comes from actually matching it on the text `diplomatic text (document)` that is split by spaces. (so "diplomatic") here. For the time being we are resorting to a hack. When we meet a visualisation that has `norm` as slug we actually look for the filename `verses`.

# Installation

Note: this app requires Python 3.10+. 
## UV Installation (preferred)

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
cd coptic
uv python install 3.12
uv sync
source .venv/bin/activate
```
And then you can run the app with either:

```sh
python ./manage.py runserver
```

if you did not activate the venv:

```sh
uv run python ./manage.py runserver
```

## Conda Installation
0. We recommend you [create a new conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands):

```sh
conda create --name cts python=3.12
conda activate cts 
```

##  1. Install requirements in development:
The preferred method is `uv sync` but you may also:

```sh
pip3 install -r requirements_django_5.txt
```

2. Update requirements:
The preferred method is `uv lock` but you may also:
```sh
pip3 install -U -r requirements.txt
pip3 freeze > requirements_django_5.txt
```

To install the search-engine:
(This has been tested with 1.11.3 and 1.12.8 )
```
curl -L https://install.meilisearch.com | sh
mv /usr/local/bin/meilisearch
```

### Configuration

All configuration that may be different between environments should be in environment variables.
You should never edit prod.py and dev.py (unless it is in order to use environemnet variables).
`git status` on production should always say something like: 

```
On branch master
Your branch is up to date with 'origin/master'.

nothing to commit, working tree clean
```

#### Environment variables:

```
export DJANGO_SECRET_KEY="" #set this to something more or less secure
export DJANGO_ALLOWED_HOSTS="" #this can be a comma separated list of hosts ("localhost,staging.data.copticscriptorium.org")
export COPTIC_ENVIROMENT="development"
export MEILI_ENV=COPTIC_ENVIROMENT
export MEILLI_MASTER_KEY="" #again something somewhat secure.
export MEILI_HTTP_ADDR=localhost:7700 # by default goes to 7700 on localhost - set differently if running elsewhere
```

Set an environment variable COPTIC_ENVIROMENT to 'production' to use production settings 
otherwise it will assume 'development'.

#### Cache location

The file-based cache is currently set both in development and production to the same value:
`/tmp/django_cache`.


### 2.  Install requirements in production:

** See the procedure above for using `uv` which is the preferred method. ** 

```sh
 pip3 install -r requirements_django_5.txt
```

Install meilisearch to `/usr/local/bin`:
```sh
curl -L https://install.meilisearch.com | sh
sudo mv meilisearch /usr/local/bin/meilisearch
```

#### Create a directory for the db

```sh
mkdir -p db
```

#### Create a systemd file from meilisearch:

This will enable running a supervised instance of meilisearch

```sh
cat << EOF > /etc/systemd/system/meilisearch.service
[Unit]
Description=Meilisearch
After=systemd-user-sessions.service

[Service]
Type=simple
WorkingDirectory=/var/lib/meilisearch
ExecStart=/usr/local/bin/meilisearch --config-file-path /etc/meilisearch.toml
User=meilisearch
Group=meilisearch
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

You may need to verify `/var/lib/meilisearch` exists and has the orrect permissions.

```
sudo mkdir -p "/var/lib/meilisearch/data.ms"
sudo chown -R meilisearch:meilisearch /var/lib/meilisearch/data.ms
```

#### Create a config file for meilisearch:

If you setup everything in env vars this can actually be an empty file.

```sh
cat << EOF > /etc/meilisearch.toml
db-path=/var/lib/meilisearch/data.ms/
http-addr=http://localhost:7700
env=production
master_key="You can set it up here, but better in an environment variable MEILI_MASTER_KEY"
EOF
```

#### Enable service:
```sh
systemctl enable meilisearch
systemctl start meilisearch
```

#### Control status
```sh
systemctl status meilisearch
```

Should be something like:
```sh
   Loaded: loaded (/etc/systemd/system/meilisearch.service; enabled; vendor preset: enabled)
   Active: active (running) since Fri 2025-01-10 14:27:49 UTC; 1min 8s ago
 Main PID: 14960 (meilisearch)
 ```

2. Run the migration to update the DB's SQL schema:

```sh
./manage.py migrate 
```

## Running tests

Github should automatically run tests on every pull request see `.github/workflows/django.yml`

```sh
./manage.py test -t .
```


## Running in development
You should now be able to run the server:

```sh
./manage.py runserver
```

If you want the search engine - it should be running first in a different terminal:

```sh
./meilisearch --env=development masterKey
```

##  Importing corpora

The import uses the github repository but first clones it locally and then uses the local copy. Everything that is used ends up in the database - so there isn't an actual production dependency on the repo being present.

If the repo is missing it will be automatically cloned. If it is already there it will be update to the latest version of the `master` branch.

To ingest texts, use the addcorpus command, and make sure that the `GITHUB_REPO_OWNER` and `GITHUB_REPO_NAME` variables are set in `coptic/settings/base.py` (although they do have default values):

```sh
./manage.py addcorpus besa-letters
```

Setting a specific path:

```sh
./manage.py addcorpus --local-repo-path=../../corpora shenoute-true
```

To add all current corpora:

```sh
./addcopora.sh ../../corpora
```

## Operations: 
### Clear Cache

You should clear the cache after deployments, before working....

```sh 
python manage.py clearcache
```

### Resetting the index.

You should also delete current search engine index from time to time. 
```sh 
python manage.py delete_index
```

### Resetting the database:
Simplest is to delete the file and run migrations.
```
rm db/sqlite3.db 
./manage.py migrate
```

# How search works

Full text search is enabled by default both in development an production. You can change that in coptic/settings/prod.py.  If the search engine fails - the app should still stay up.

We are using https://www.meilisearch.com an open source search engine written in Rust that offers a good mix of capabilities, performance and ease of operations.

The Coptic keyboard is implementefd using https://keyman.com and is included in [](templates/base.html) we load three configurations cop-copt, cop and en and attach by default to all text boxes.

We have a to_json method added on the [Text](texts/models.py) model, it includes the main fields as well as the "text_meta" fields extracted from the SGML and the lemmatized as well as normalized and normalized_group versions of the text (that we "flatten" by chapter).

We index each text with all of its metadata and within the retrievel implemented in [ft_search](texts/ft_search.py) we retrieve the matched positions as well as the highlighting of the search terms. 

We have a small javascript snippet (in base.html) that scrolls down to the first exact match for the query term.

We reduce each result with  [reduce_text_with_ellipsis](texts/ft_search.py) the logic of the implementation is, given n number of words keep: 1. the first n words of the document, n words around each highlighted search term, the last n words of the document. By default n is `10`. This implementation allows for good context - while keeping each result relatively short.

* Results are sorted by decreasing number of matched query terms. 
* Returns documents that contain all query terms first.
* Results are sorted by increasing number of typos. Returns documents that match query terms with fewer typos first.

The documents we are indexing have the following format:
```python
[
    {
        "id": 33031,
        "title": "Acts of Pilate-Gospel of Nicodemus CM.1643 part 1",
        "slug": "acts-of-pilate-gospel-of-nicodemus-cm1643-part-1",
        "created": "2025-01-15T09:18:25.020424",
        "modified": "2025-01-15T09:18:25.056685",
        "corpus": "Acts of Pilate - Gospel of Nicodemus",
        "corpus_slug": "actspilate",
        "text_meta": {
            "Coptic_edition": "<a href='https://babel.hathitrust.org/cgi/pt?id=coo.31924028715617&seq=10'>Lacau 1904</a>",
            "OrigDate_notBefore": "901",
            "Trismegistos": "none",
            "annotation": "Lydia Bremer-McCollum, Nicholas Wagner",
            "author": "Anonymous",
            "collection": "Manuscrits coptes",
            "corpus": "acts.pilate",
            "country": "Egypt",
            "document_cts_urn": "urn:cts:copticLit:misc.acts_pilate.lacau_ed:9",
            "idno": "129/17 f. 50",
            "language": "Sahidic Coptic",
            "license": "<a href='https://creativecommons.org/licenses/by/4.0/'>CC-BY 4.0</a>",
            "msName": "CM.1643",
            "next": "urn:cts:copticLit:misc.acts_pilate.lacau_ed:10-11",
            "note": "Coptic follows Lacau's transcription. Chapter divisions follow paragraph breaks in Lacau's translation. No CMCL manuscript siglum exists for this codex, so the MsName is the CLM number in PATHS.",
            "objectType": "codex",
            "ocr": "automatic",
            "order": "1",
            "origDate": "between 901 and 1100",
            "origDate_notAfter": "1100",
            "origDate_precision": "medium",
            "origPlace": "White Monastery",
            "pages_from": "27",
            "pages_to": "28",
            "parsing": "automatic",
            "paths_authors": "none",
            "paths_manuscripts": "<a href='http://paths.uniroma1.it/atlas/manuscripts/1643'>1643</a>",
            "paths_works": "<a href='http://paths.uniroma1.it/atlas/works/35'>35</a>",
            "placeName": "Atripe",
            "project": "Coptic SCRIPTORIUM",
            "redundant": "no",
            "repository": "Paris Bibliothéque Nationale",
            "segmentation": "automatic",
            "source": "<a href='https://babel.hathitrust.org/cgi/pt?id=coo.31924028715617&seq=10'>Lacau 1904</a>",
            "source_info": "OCR of Lacau pdf on Hathitrust using OCR4all",
            "tagging": "automatic",
            "title": "Acts of Pilate-Gospel of Nicodemus CM.1643 part 1",
            "translation": "none",
            "version_date": "2024-10-31",
            "version_n": "6.0.0",
            "witness": "2 other manuscripts contain this work but are not published by Coptic Scriptorium",
        },
        "text": [
            {
                "lemmatized": "ϫⲉ ⲁ ⲟⲩ ⲥⲧⲁⲥⲓⲥ ϣⲱⲡⲉ ... ⲛⲧⲟⲟⲩ ⲱϣ ⲉⲃⲟⲗ",
                "normalized": "ϫⲉ ⲁ ⲟⲩ ⲥⲧⲁⲥⲓⲥ ϣⲱⲡⲉ ... ⲁ ⲩ ⲱϣ ⲉⲃⲟⲗ",
                "normalized_group": "ϫⲉⲁⲟⲩⲥⲧⲁⲥⲓⲥ ϣⲱⲡⲉ ... · ⲁⲩⲱϣ ⲉⲃⲟⲗ",
            }
        ],
        "tt_dir": "acts-pilate",
        "tt_filename": "pilate.1643.27-28.tt",
        "tt_dir_tree_id": "c5513bbe70dfa745bb49c55ef88862af6dfc0981",
        "document_cts_urn": "",
    },
    { "id": ...
    },
]
```

In development you can visit http://localhost:7700 for a rich interface that will allow you to explore the index.

The built-in ranking rules are:
```
[
  "words", 
  "typo",  
  "proximity",
  "attribute",
  "sort",
  "exactness",
  "release_date:desc"
]
```

In the `__init__` method of the  `Search` class you have a all of the possible options, commented-out - including stop words and the likes.

## Project Structure
```
├── README.md -- This file
├── addcorpora.sh - a script to import all corpora
├── compare_prod_to_stage.py - a script to compare staging to production
├── coptic
│   ├── settings contains base.py with common settings dev.py for development settings and prod.py for production.
│   ├── urls.py - URL routing configuration
│   ├── views.py - The view layer - including the search implementation
│   └── wsgi.py - Launcher for wsgi
├── data.ms - in development the locaiton of the meilisearch index files
├── db - in production the locaiton of the sqlite database
├── dumps - in development location of meilisearch dump files
├── gh_ingest - the implementation of ingestion/scraping/import
│   ├── corpus_scraper.py - the main scraper implementation
│   ├── corpus_transaction.py -  implementation of  transactional logic (probably not actually needed)
│   ├── docs - documentation on the visualisation generation
│   ├── htmlvis.py - implementation of the visualisation generation
│   ├── management - django management commands
│   ├── repository.py - class to reperesent the github repository
│   ├── scraper_exceptions.py - class to exceptions to the import process
│   ├── test_generate_visualisation.py  - tests for visualisation
│   ├── test_htmlvis.py  - tests for visualisation
│   └── test_scraper.py  - tests for scraper
├── manage.py  - base django management utility
├── meilisearch - in development the meilisearch executable
├── nav.py - a script to update the navigation header
├── package.json - javascript dependecies
├── requirements.txt  - unlocked dependecies - to be used in development only
├── requirements_django_5.txt  - locked dependecies - to be used in production after testing in staging
├── sqlite3.db - database file in development
├── static - static resources (javascript, css)
├── templates - html templates
└── texts - implementation of the models etc.
    ├── admin.py - Admin interface configuration (/admin)
    ├── ft_search.py - Implementation of fulltext search
    ├── management - Implementation of django commands
    ├── migrations - Django database migrations
    ├── models.py  - Data models
    ├── search_fields.py - probably shouyld be removed at some point - implementation of facets using sqlite
    ├── test_ft_search.py - tests for full text
    ├── test_urn.py - tests for full stable urns
    ├── tests - test_models.py tests for full stable urns
    └── urn.py - implementation for stable urns
```