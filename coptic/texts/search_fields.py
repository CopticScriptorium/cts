from texts.models import SpecialMeta, TextMeta


class SearchField:
	def __init__(self, title):
		self.title = title
		self.values = TextMeta.objects.filter(name=title).values_list('value', flat=True).distinct().order_by('value')


def get_search_fields():
	'Get the search fields for the search tools in the site header. Sort using the order from SpecialMeta.'

	all_sm = SpecialMeta.objects.all()
	order_by_name = {sm.name: sm.order for sm in all_sm}

	search_fields = [SearchField(name) for name in order_by_name.keys()]
	order_and_fields = [(order_by_name[sf.title], sf) for sf in search_fields]
	order_and_fields.sort()  # Using the first element of the tuple, the order
	sorted_search_fields = [oaf[1] for oaf in order_and_fields]

	return sorted_search_fields
