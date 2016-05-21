"""Short python script to prepopulate the database with Annis and Corpora
information."""

import os
import sys
import django

def do_config():
    """Does the initial configuration of the database."""
    sys.path.insert(0, '/var/www/cts/coptic/')

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coptic.settings")
    #os.environ["DJANGO_SETTINGS_MODULE"] = "coptic.settings"

    django.setup()

    import helper

    # create the annis server configuration
    helper.create_annis_server()

    # predefine the known corpora
    helper.load_known_corpora()

    # define the known visualizations
    helper.define_visualizations()

    # now find the visualizations available for the corpora
    helper.find_corpora_visualizations()

    # pre-load the critical search fields.
    helper.load_searchfields()

    from ingest import ingest
    from ingest.models import Ingest

    new_ingest = Ingest.objects.create()
    # new_ingest.save()

    ingest.fetch_texts(new_ingest.id)

if __name__ == "__main__":
    do_config()
