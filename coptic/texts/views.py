from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from texts.models import Text, Collection, SearchField, SearchFieldValue
from texts.search_fields import get_search_fields
from ingest.models import Ingest

# Both the list and the single views should render index.html for the client side app 
def list(request, slug):
	search_fields = get_search_fields()
	context = { 
					'body_class' : "index",
					'texts' : [],
					'search_fields' : search_fields[0:5],
					'secondary_search_fields' : search_fields[5:]
				}
	return render(request, 'index.html', context) 

def single(request, slug):
	search_fields = get_search_fields()
	context = { 
					'body_class' : "index",
					'texts' : [],
					'search_fields' : search_fields[0:5],
					'secondary_search_fields' : search_fields[5:]
				}
	return render(request, 'index.html', context) 

