from django.core.management.base import BaseCommand
from texts.models import (
    Corpus
)

class Command(BaseCommand):
    help = 'Full Text Index all corpora'

    def handle(self, *args, **kwargs):
        #FIXME: it's actually probably better to first
        # create a text_pairs list and then index all of them
        # at once.
        for corpus in Corpus.objects.all():
            corpus.index()
            self.stdout.write(f'Corpus {corpus.slug} indexed\n')