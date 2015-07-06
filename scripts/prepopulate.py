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

    print ("Loading Corpora")
    from texts.models import Corpus

    print ("Loading AnnisServer")
    from annis.models import AnnisServer
    from ingest import ingest

    print ("Looping through AnnisServers...")
    try:
        annis = AnnisServer.objects.get(base_domain__exact='https://corpling.uis.georgetown.edu')
    except AnnisServer.DoesNotExist:
        print("Saving a new instance of ANNIS Server")
        annis = AnnisServer.objects.create()
        annis.title = 'Georgetown Annis'
        annis.base_domain = 'https://corpling.uis.georgetown.edu'
        annis.corpus_metadata_url = "annis-service/annis/meta/corpus/:corpus_name"
        annis.corpus_docname_url = "annis-service/annis/meta/docnames/:corpus_name"
        annis.document_metadata_url = "annis-service/annis/meta/doc/:corpus_name/:document_name"
        annis.html_visualization_url = "annis/embeddedvis/htmldoc/:corpus_name/:document_name?config=:html_visualization_format"
        annis.save()

    known_corpora = ["shenoute.a22", "apophthegmata.patrum", "shenoute.abraham.our.father",
        "besa.letters", "shenoute.fox", "sahidica.mark", "sahidica.1corinthians",
        "sahidica.nt", "shenoute.eagerness"]

    for one_corpora in known_corpora:
        try:
            Corpus.objects.get(annis_corpus_name__exact='one_corpora')
        except Corpus.DoesNotExist:
            corpus = Corpus.objects.create()
            corpus.annis_corpus_name = one_corpora
            corpus.save()

    from ingest.models import Ingest    
    new_ingest = Ingest.objects.create()
    new_ingest.save()

    ingest.fetch_texts(new_ingest.id)

if __name__ == "__main__":
    do_config()
