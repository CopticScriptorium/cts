"""
expire.py

Expire from their source lists in ANNIS

"""

def expire_ingest(expire_ingest_instance):

    """
    Set all texts is_expired value to true
    """

    from texts.models import Text

    for text in Text.objects.all():

        text.is_expired = True
        text.save()

