"""Helper python script that complements the prepopulate script.

Assumes that the Django application has already been configured, so
that import commands can operate at the top of the file."""

from annis.models import AnnisServer
from texts.models import Corpus
from texts.models import HtmlVisualizationFormat
from texts.models import SearchField
import xml.etree.ElementTree as ET
from urllib import request

def create_annis_server():
    """Creates default ANNIS server information."""
    try:
        annis = AnnisServer.objects.get(base_domain__exact=
                                        'https://corpling.uis.georgetown.edu')
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
    """Defines known corpora in advance.

    For various reasons, we don't want to query the ANNIS server for available corpora:
    They're not ready for the URN resolver. Certain metadata about them isn't available
    from ANNIS, such as the urn_code."""

    print ("Loading Corpora")

    # For debugging purposes, comment out the definition of all but say the first
    # corpus, to speed the ingest time.
    shenoute_a22 = Corpus()
    shenoute_a22.annis_corpus_name = "shenoute.a22"
    shenoute_a22.title = "Acephalous Work 22"
    shenoute_a22.slug = "acephalous_work_22"
    shenoute_a22.urn_code = "shenoute.a22"
    shenoute_a22.github = "https://github.com/CopticScriptorium/corpora/tree/master/shenoute-a22"

    patrum = Corpus()
    patrum.annis_corpus_name = "apophthegmata.patrum"
    patrum.title = "Apophthegmata Patrum"
    patrum.slug = "ap"
    patrum.urn_code = "ap"
    patrum.github = "https://github.com/CopticScriptorium/corpora/tree/master/AP"

    saof = Corpus()
    saof.annis_corpus_name = "shenoute.abraham.our.father"
    saof.title = "Abraham Our Father"
    saof.slug = "abraham_our_father"
    saof.urn_code = "shenoute.abraham"
    saof.github = "https://github.com/CopticScriptorium/corpora/tree/master/abraham"

    besa_ap = Corpus()
    besa_ap.annis_corpus_name = "besa.letters"
    besa_ap.title = "Letter to Aphthonia"
    besa_ap.slug = "to_aphthonia"
    besa_ap.urn_code = "besa.aphthonia"
    besa_ap.github = "https://github.com/CopticScriptorium/corpora/tree/master/besa-letters"

    fox = Corpus()
    fox.annis_corpus_name = "shenoute.fox"
    fox.title = "Not Because a Fox Barks"
    fox.slug = "not_because_a_fox_barks"
    fox.urn_code = "shenoute.fox"
    fox.github = "https://github.com/CopticScriptorium/corpora/tree/master/shenoute-fox"

    mark = Corpus()
    mark.annis_corpus_name = "sahidica.mark"
    mark.title = "Gospel of Mark"
    mark.slug = "gospel_of_mark"
    mark.urn_code = "nt.mark"
    mark.github = "https://github.com/CopticScriptorium/corpora/tree/master/bible"

    corinth = Corpus()
    corinth.annis_corpus_name = "sahidica.1corinthians"
    corinth.title = "1 Corinthians"
    corinth.slug = "1st_corinthians"
    corinth.urn_code = "nt.1cor"
    corinth.github = "https://github.com/CopticScriptorium/corpora/tree/master/bible"

    snt = Corpus()
    snt.annis_corpus_name = "sahidica.nt"
    snt.title = "New Testament"
    snt.slug = "new-testament"
    snt.urn_code = "nt"
    snt.github = "https://github.com/CopticScriptorium/corpora/tree/master/bible"

    eager = Corpus()
    eager.annis_corpus_name = "shenoute.eagerness"
    eager.title = "I See Your Eagerness"
    eager.slug = "eagernesss"
    eager.urn_code = "shenoute.eagerness"
    eager.github = "https://github.com/CopticScriptorium/corpora/tree/master/shenoute-eagerness"

    besa_nuns = Corpus()
    besa_nuns.annis_corpus_name = "besa.letters"
    besa_nuns.title = "Letter to Thieving Nuns"
    besa_nuns.slug = "to_thieving_nuns"
    besa_nuns.urn_code = "besa.thieving"
    besa_nuns.github = "https://github.com/CopticScriptorium/corpora/tree/master/besa-letters"

    doc_pap = Corpus()
    doc_pap.annis_corpus_name = "doc.papyri"
    doc_pap.title = "Documentary Papyri"
    doc_pap.slug = "papyri"
    doc_pap.urn_code = "copticDoc:papyri_info"
    doc_pap.github = "https://github.com/CopticScriptorium/corpora/tree/master/doc-papyri"

    known_corpora = [shenoute_a22, patrum, saof, besa_ap, fox, mark, corinth, snt, eager, besa_nuns, doc_pap]
#    known_corpora = [shenoute_a22]
    
    for one in known_corpora:
        try:
            Corpus.objects.get(slug__exact=one.slug)
        except Corpus.DoesNotExist:
            one.save()

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
    """Finds the visualizations for each corpora from ANNIS, and copies the data
    into the database for later reference."""

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

def load_searchfields():
    """Prepopulates the database with search fields that we care about in the
    web user interface.
    
    This is essential because two of the search fields need to have the
    splittable property properly set, or the data won't be ingested properly.
    """
    
    corpus = SearchField()
    corpus.title = "corpus"
    corpus.order = 1
    
    author = SearchField()
    author.title = "author"
    author.order = 2

    ms_name = SearchField()
    ms_name.title = "msName"
    ms_name.order = 3

    annotation = SearchField()
    annotation.title = "annotation"
    annotation.order = 4
    annotation.splittable = ","

    translation = SearchField()
    translation.title = "translation"
    translation.order = 5
    translation.splittable = ","
    
    for searchfield in [corpus, author, ms_name, annotation, translation]:
        try:
            SearchField.objects.get(title__exact=searchfield.title)
        except SearchField.DoesNotExist:
            searchfield.save()
