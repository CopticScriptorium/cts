"""Short python script to prepopulate the database with Annis and Corpora
information."""

import os
import sys
import django

def do_config():
    """Does the initial configuration of the database."""
    sys.path.insert(0, os.getcwd())

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coptic.settings")

    django.setup()

    import helper

    # define the known visualizations
    helper.define_visualizations()

    # pre-load the critical search fields.
    helper.load_searchfields()

if __name__ == "__main__":
    do_config()
