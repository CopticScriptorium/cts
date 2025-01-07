# Installation

Note: this app requires Python 3.8+. 

0. We recommend you [create a new conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands):

```sh
conda create --name cts python=3.12
conda activate cts 
```

1. Install requirements:

```sh
pip install -r requirements_django_5.txt
```

2. Update requirements:
```sh
pip install -U -r requirements.txt
pip freeze > requirements_django_5.txt
```

For search:
````
curl -L https://install.meilisearch.com | sh
./meilisearch --master-key=$MEILLI_MASTER_KEY
```

## Configuration

1. Create a copy of the `secrets.py` file and edit it with your information:

```sh
cp coptic/settings/secrets.py.example coptic/settings/secrets.py
vim coptic/settings/secrets.py
```

Set an environment variable COPTIC_ENVIROMENT to 'prod' to use production settings 
otherwise it will assume 'dev'

2. Run the migration to update the DB's SQL schema:

```sh
python manage.py migrate 
```

## Running tests

Github should automatically run tests on every pull request see `.github/workflows/django.yml`

```sh
python manage.py test -t .
```


## Running
You should now be able to run the server:

```sh
python manage.py runserver
```

To ingest texts, use the addcorpus command, and make sure that the `GITHUB_REPO_OWNER` and `GITHUB_REPO_NAME` variables are set in `coptic/settings/base.py`:

```sh
python manage.py addcorpus besa-letters
```

You can also checkout the corpora locally and do a local import which should be _much_ faster.

```sh
python manage.py addcorpus --source=local --local-repo-path=../../corpora shenoute-true
```

To add all current corpora

```sh
./addcopora.sh
```
# Clear Cache

You should clear the cache after deployments.

```sh 
python manage.py clearcache
```

## How search works

We have a to_json method added on the Text model, it included the main fields as well as the "text_meta" fields extracted from the SGML and the lemmatized as well as normalized versions of the text (that we "flatten").

We index each text with all of its metadata and withing the retrievel implemented in texts/ft_search we retrieve the matched positions as well as the highlighting of the search terms.
