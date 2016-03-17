from django.shortcuts import render
from texts.search_fields import get_search_fields


def list(request):
	search_fields = get_search_fields()
	context = { 
					'body_class' : "index",
					'texts' : [],
					'search_fields' : search_fields[0:5],
					'secondary_search_fields' : search_fields[5:]
				}
	return render(request, 'index.html', context) 
