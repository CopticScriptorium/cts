"""Helper python script that complements the prepopulate script.

Assumes that the Django application has already been configured, so
that import commands can operate at the top of the file."""

from annis.models import AnnisServer
from texts.models import Corpus
from texts.models import HtmlVisualizationFormat
import xml.etree.ElementTree as ET
from urllib import request

def create_annis_server():
    from annis.models import AnnisServer
    from ingest import ingest

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

def load_known_corpora():
    """The corpora need to be defined in advance. For various reasons, we don't want
    to query the annis server for available corpora, because there may be reasons not
    to treat them with this tool yet."""
    
    print ("Loading Corpora")

    known_corpora = ["shenoute.a22", "apophthegmata.patrum", "shenoute.abraham.our.father",
        "besa.letters", "shenoute.fox", "sahidica.mark", "sahidica.1corinthians",
        "sahidica.nt", "shenoute.eagerness"]

    for one_corpora in known_corpora:
        try:
            Corpus.objects.get(annis_corpus_name__exact=one_corpora)
        except Corpus.DoesNotExist:
            corpus = Corpus.objects.create()
            corpus.annis_corpus_name = one_corpora
            corpus.save()

def define_visualizations():
    """Unfortunately, these mappings are defined in the database, when they probably
    should be defined in code. This routine pre-populates the database with the expected
    visualizations."""
    
    norm = HtmlVisualizationFormat()
    norm.slug = "norm"
    norm.button_title = "normalized"
    norm.title = "Normalized Text"
    
    analytic = HtmlVisualizationFormat()
    analytic.slug = "analytic"
    analytic.button_title = "analytic"
    analytic.title = "Analytic Visualization"

    dipl = HtmlVisualizationFormat()
    dipl.slug = "dipl"
    dipl.button_title = "diplomatic"
    dipl.title = "Diplomatic Edition"

    sahidica = HtmlVisualizationFormat()
    sahidica.slug = "sahidica"
    sahidica.button_title = "chapter"
    sahidica.title = "Sahidica Chapter View"
    
    for vis in [norm, analytic, dipl, sahidica]:
        try:
            HtmlVisualizationFormat.objects.get(slug__exact=vis.slug)
        except HtmlVisualizationFormat.DoesNotExist:
            vis.save()

def find_corpora_visualizations():

    # build a quick map of visualizations, so that we can reference by annis label.    
    vis_map = dict()
    for vis in HtmlVisualizationFormat.objects.all():
        vis_map[vis.slug] = vis

    for corpus in Corpus.objects.all():
        
        # get the list of all the visualizations already loaded for this corpus.
        already_have = set()
        for one_fmt in corpus.html_visualization_formats.all():
            already_have.add(one_fmt.slug)

        url_fmt = "https://corpling.uis.georgetown.edu/annis-service/annis/query/resolver/{0}/NULL/node"
        url_to_fetch = url_fmt.format(corpus.annis_corpus_name)
        res = request.urlopen(url_to_fetch)
        root = ET.fromstring(res.read())
        xpath = "./resolverEntry[visType='htmldoc']/mappings/entry/value"
        added = False
        for one_node in root.findall(xpath):
            vis_slug = one_node.text
            if vis_slug not in already_have:
                corpus.html_visualization_formats.add(vis_map[vis_slug])
                added = True
        
        # If we added any visualizations, save them now
        if added:
            corpus.save()
