
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
