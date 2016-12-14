import datetime
import logging
from django.db import models
from ingest.expire import expire_ingest
from ingest.tasks import ingest_asynch
from texts.models import Corpus


class Ingest(models.Model):
    """
    Model for creating new ingests of documents and metadata

    """
    created                 = models.DateTimeField(editable=False)
    modified                = models.DateTimeField(editable=False)
    corpora                 = models.ManyToManyField(Corpus)
    num_corpora_ingested    = models.PositiveIntegerField(default=0, editable=False)
    num_texts_ingested      = models.PositiveIntegerField(default=0, editable=False)

    def __str__(self):
        return self.created.strftime('%H:%S %d.%b.%Y')

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        first_save = not self.id
        if first_save:
            self.created = datetime.datetime.today()
        self.modified = datetime.datetime.today()

        super(Ingest, self).save(*args, **kwargs)

        if first_save:
            ingest_asynch(self.id)

class ExpireIngest(models.Model):
    """
    Model for expiring ingests

    """
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField(editable=False)

    def __str__(self):
        return self.created.strftime('%H:%S %d.%b.%Y')

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = datetime.datetime.today()
        self.modified = datetime.datetime.today()

        # Set up an instance of the logger
        logger = logging.getLogger(__name__)

        logger.info(" -- Ingest: Deleting all previous ingest expirations")
        ExpireIngest.objects.all().delete()

        super(ExpireIngest, self).save(*args, **kwargs)
        expire_ingest(self.id)
