from django.shortcuts import render
from texts.search_fields import get_search_fields


def home(request):
    'Home/index view'

    search_fields = get_search_fields()
    context = {
        'body_class':               "text-list",
        'search_fields':            search_fields[0:5],
        'secondary_search_fields':  search_fields[5:]
    }

    return render(request, 'index.html', context)


def not_found(request):
    return render(request, '404.html', {})
