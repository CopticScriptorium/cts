import re
from django.conf.urls import include, url
from django.urls import path
from django.contrib import admin
from django.shortcuts import redirect
import coptic.views as views
from django.conf import settings
from django.conf.urls.static import static


def _redirect_citation_urls(request, url_except_data_type, data_type):
    'Redirect all the "permanent" citation URLs (annis, relannis, visualizations, etc.) to internal URLs'

    new_loc = "/"  # In case we fail
    parts_split_by_slash = url_except_data_type.split("/")
    all_but_last_part = "/".join(parts_split_by_slash[0:-1])
    last_part = parts_split_by_slash[-1]

    cts_urn = (
        all_but_last_part if data_type in ("html", "xml") else url_except_data_type
    )

    texts = views.texts_for_urn(cts_urn)

    if len(texts) > 0:
        text = texts[0]
        if data_type == "annis":
            new_loc = text.corpus.annis_link()
        elif data_type == "html":
            new_loc = "/texts/" + text.corpus.slug + "/" + text.slug + "/" + last_part
        elif data_type in ("relannis", "paula/xml", "tei/xml"):
            new_loc = text.corpus.github + "/" + text.corpus.annis_corpus_name + "_"
            new_loc += (
                "ANNIS"
                if data_type == "relannis"
                else "PAULA" if data_type == "paula/xml" else "TEI"
            )
            if re.search(r"(\.ot|\.nt)$", text.corpus.annis_corpus_name):
                new_loc += ".zip"

    return redirect(new_loc)


urlpatterns = [
    url(r"^grappelli/", include("grappelli.urls")),
    url(r"^admin/", admin.site.urls),
    # Using path() for modern URL patterns
    path("search/", views.search, name="search"),
    path("index/<str:special_meta>/", views.index_view, name="index"),
    path("texts/<slug:corpus>/", views.corpus_view, name="corpus"),
    path("texts/<slug:corpus>/<slug:text>/", views.text_view, name="text"),
    path(
        "texts/<slug:corpus>/<slug:text>/<str:format>/",
        views.text_view,
        name="text_with_format",
    ),
    # Legacy URL patterns using url()
    url(r"^(.*)/(annis|relannis|tei/xml|paula/xml|html)$", _redirect_citation_urls),
    url(r"^(?P<urn>urn:.*)/$", views.urn, name="urn"),
    url(r"^$", views.home_view, name="home"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
