"""Helper python script that complements the prepopulate script.

Assumes that the Django application has already been configured, so
that import commands can operate at the top of the file."""

from texts.models import HtmlVisualizationFormat
from texts.models import SpecialMeta

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

def load_searchfields():
    """Prepopulates the database with search fields that we care about in the
    web user interface.
    
    This is essential because two of the search fields need to have the
    splittable property enabled, or the data won't be ingested properly.
    """
    
    corpus = SpecialMeta()
    corpus.title = "corpus"
    corpus.order = 1
    
    author = SpecialMeta()
    author.title = "author"
    author.order = 2

    ms_name = SpecialMeta()
    ms_name.title = "msName"
    ms_name.order = 3

    annotation = SpecialMeta()
    annotation.title = "annotation"
    annotation.order = 4
    annotation.splittable = True

    translation = SpecialMeta()
    translation.title = "translation"
    translation.order = 5
    translation.splittable = True

    for field in [corpus, author, ms_name, annotation, translation]:
        try:
            SpecialMeta.objects.get(name=field.name)
        except SpecialMeta.DoesNotExist:
            field.save()
