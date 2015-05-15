import pdb

# Retrieve a list of searchfields for the search toolbar
def get_search_fields():
	"""
	Get the search fields for the search tools in the site header
	"""
	from texts.models import SearchField, SearchFieldValue


	search_fields = SearchField.objects.all().order_by("order")
	for search_field in search_fields:
		search_field.values = SearchFieldValue.objects.filter( search_field=search_field.id ) 

	return search_fields 


# Populating values for the search fields
def populate_values( instance ):

	from texts.models import Text, SearchField, SearchFieldValue

	if instance.splittable:

		split_sfvs = []
		sfvs = SearchFieldValue.objects.filter( search_field=instance.id )

		# for each search field value, split it on the splittable field
		for sfv in sfvs:

			# Split the search field value on the splittable field
			split_values = sfv.value.split( instance.splittable )
			sfv_texts = list( sfv.texts.all() )

			# For each value, in the split values, add its data to the split sfvs list
			for value in split_values:

				val_is_in_split_sfvs = False
				value = value.strip()

				for split_sfv in split_sfvs:
					if value == split_sfv['value']:
						val_is_in_split_sfvs = True 
						for sfv_text in sfv_texts:
							if sfv_text not in split_sfv['texts']:
								split_sfv['texts'].append(sfv_text)

				if not val_is_in_split_sfvs:
					split_sfvs.append({
							'value' : value,
							'texts' : sfv_texts[:]
						})

		# Remove the old Search Field Values
		SearchFieldValue.objects.filter(search_field=instance.id).delete()

		# Create new search field values based on the original search field value
		for split_sfv in split_sfvs:

			# Create a new search field
			sfv = SearchFieldValue()

			# Add the search field instance to the sfv
			sfv.search_field = instance

			# Set the split value and title
			sfv.value = split_sfv['value'] 
			sfv.title = split_sfv['value']

			# Save so we have an pk id no for adding the manytomany field texts 
			sfv.save()

			# Search field texts
			for text in split_sfv['texts']:

				# Add the texts via the native add ManyToMany handling
				sfv.texts.add( text )

			# Save the updates
			sfv.save()


	return True	 
