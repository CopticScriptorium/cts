
# TODO: review this logic and make sure it's correct for all documents.
def cts_work(doc_urn):
	urn_parts = doc_urn.split(":")
	return ":".join(urn_parts[0:3]) # e.g., "urn:cts:copticLit"

def textgroup_urn(doc_urn):
	urn_parts = doc_urn.split(":")
	urn_dot_parts = urn_parts[3].split(".")
	return cts_work(doc_urn) + ":" + urn_dot_parts[0]

def corpus_urn(doc_urn):
	urn_parts = doc_urn.split(":")
	urn_dot_parts = urn_parts[3].split(".")
	return textgroup_urn(doc_urn) + "." + urn_dot_parts[1]

def parts(doc_urn):
	"""A flat list of all "parts", which are defined as top-level colon-delimited parts, further
        split by dot-delimited parts, e.g.:

		urn:cts:copticLit:psathanasius.matthew20.budge:1:56
		->
		['urn', 'cts', 'copticLit', 'psathanasius', 'matthew20', 'budge', '1', '56']
	"""
	return [part for chunk in doc_urn.split(":") for part in chunk.split(".")]

def partial_parts_match(urn1, urn2):
	""" True iff all parts of urn1 exactly match all parts of urn2.
	If one is longer than the other, only overlapping parts are considered. """
	parts1 = parts(urn1)
	parts2 = parts(urn2)
	i = min(len(parts1), len(parts2))
	return all(p1 == p2 for p1, p2 in zip(parts1[:i], parts2[:i]))
