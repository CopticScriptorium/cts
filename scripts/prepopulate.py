"""Short python script to prepopulate the database with Annis and Corpora
information."""

import os
import sys
from django.core.exceptions import ObjectDoesNotExist
import django

def do_config():
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
    
    from ingest import ingest
    from ingest.models import Ingest
    
    new_ingest = Ingest.objects.create()
    new_ingest.save()

    ingest.fetch_texts(new_ingest.id)

if __name__ == "__main__":
    do_config()
