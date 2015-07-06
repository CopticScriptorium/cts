from celery import shared_task
from ingest.ingest import fetch_texts
from ingest.expire import ingest_expired_text 

# Spawn instance in background with celery
@shared_task
def shared_task_spawn_ingest( ingest_id ):
    fetch_texts( ingest_id )

@shared_task
def shared_task_spawn_single_ingest( text_id ):
    ingest_expired_text( text_id )
