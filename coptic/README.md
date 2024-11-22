# Installation

Note: this app requires Python 3.6+. 

0. We recommend you [create a new conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands):

```sh
conda create --name cts python=3.7
conda activate cts 
```

1. Install requirements:

```sh
pip install -r requirements_django_2.txt
```

## Configuration

1. Create a copy of the `secrets.py` file and edit it with your information:

```sh
cp coptic/settings/secrets.py.example coptic/settings/secrets.py
vim coptic/settings/secrets.py
```

2. Run the migration to update the DB's SQL schema:

```sh
python manage.py migrate 
```

## Running tests

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
