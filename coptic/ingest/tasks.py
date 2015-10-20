import threading
from ingest.ingest import fetch_texts
from ingest.expire import ingest_expired_text 

def ingest_asynch( ingest_id ):
    threading.Thread(target=fetch_texts, args=(ingest_id,)).start()

def single_ingest_asynch( text_id ):
    threading.Thread(target=ingest_expired_text, args=(text_id,)).start()
