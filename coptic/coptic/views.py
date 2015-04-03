from django.shortcuts import render
from django.http import HttpResponse
from texts.models import Text


def home(request):
	"""
	Home/index view
	"""

	from texts.search_fields import get_search_fields
	
	texts = Text.objects.order_by('-created')[:15]
	search_fields = get_search_fields()
	context = { 
					'body_class' : "text-list",
					'texts' : texts,
					'search_fields' : search_fields[0:5],
					'secondary_search_fields' : search_fields[5:]
				}
				
	return render(request, 'index.html', context) 

def not_found(request):
	"""
	404 view
	"""
	from texts.search_fields import get_search_fields
	
	search_fields = get_search_fields()
	context = { 
					'body_class' : "text-list",
					'texts' : [],
					'search_fields' : search_fields[0:5],
					'secondary_search_fields' : search_fields[5:]
				}
				
	return render(request, '404.html', context) 

