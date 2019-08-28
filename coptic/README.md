# Installation

Note: this app requires Python 3.6+. 

0. We recommend you [create a new conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands) for Xposition:

```sh
conda create --name cts python=3.7
conda activate cts 
```

1. Install requirements:

```sh
pip install -r requirements.txt
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

3. Run the script to prepopulate the DB:

```sh
python ../scripts/prepopulate.py
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

