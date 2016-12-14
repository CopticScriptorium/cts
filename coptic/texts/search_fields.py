from texts.models import SpecialMeta, TextMeta


class SearchField:
	def __init__(self, title, splittable):

		def get_parts(multi_part_values):
			for val in multi_part_values:
				parts = val.split(',')
				for part in parts:
					yield part.strip()

		self.title = title
		pre_split_values = TextMeta.objects.filter(name=title).values_list('value', flat=True).distinct().order_by('value')
		self.values = sorted(set(get_parts(pre_split_values))) if splittable else pre_split_values


def get_search_fields():
	'Get the search fields for the search tools in the site header. Sort using the order from SpecialMeta.'

	all_sm = SpecialMeta.objects.all()
	splittable = [sm.name for sm in all_sm if sm.splittable]
	order_by_name = {sm.name: sm.order for sm in all_sm}

	search_fields = [SearchField(name, name in splittable) for name in order_by_name.keys()]
	order_and_fields = [(order_by_name[sf.title], sf) for sf in search_fields]
	order_and_fields.sort()  # Using the first element of the tuple, the order
	sorted_search_fields = [oaf[1] for oaf in order_and_fields]

	return sorted_search_fields
