import threading
from ingest.ingest import fetch_texts

def ingest_asynch( ingest_id ):
    threading.Thread(target=fetch_texts, args=(ingest_id,)).start()
