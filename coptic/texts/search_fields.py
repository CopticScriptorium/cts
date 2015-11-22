def get_search_fields():
	"""
	Get the search fields for the search tools in the site header
	"""
	from texts.models import SearchField, SearchFieldValue

	search_fields = SearchField.objects.all().order_by("order")
	for search_field in search_fields:
		search_field.values = SearchFieldValue.objects.filter( search_field=search_field.id ) 

	return search_fields 
