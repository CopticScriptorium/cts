from texts.models import SpecialMeta, SearchField, SearchFieldValue


def get_search_fields():
	'Get the search fields for the search tools in the site header. Sort using the order from SpecialMeta.'

	order_by_name = {sm.name: sm.order for sm in SpecialMeta.objects.all()}
	search_fields = SearchField.objects.filter(title__in=order_by_name.keys())
	order_and_fields = [(order_by_name[sf.title], sf) for sf in search_fields]
	order_and_fields.sort()  # Using the first element of the tuple, the order
	sorted_search_fields = [oaf[1] for oaf in order_and_fields]

	for search_field in sorted_search_fields:
		search_field.values = SearchFieldValue.objects.filter(search_field=search_field.id)

	return sorted_search_fields
