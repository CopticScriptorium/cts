from django.core.management.base import BaseCommand
from texts.models import (
    Corpus
)

class Command(BaseCommand):
    help = 'Full Text Index a corpus'
    def add_arguments(self, parser):
        parser.add_argument(
            'corpus_dirnames',
            nargs='+',
            type=str,
            help="The names of a top-level directory inside of the corpus GitHub repository to index"
        )

    def handle(self, *args, **options):
        for corpus_dirname in options["corpus_dirnames"]:
            self.stdout.write(f'index {corpus_dirname} \n')
            corpus = Corpus.objects.filter(annis_corpus_name__iexact=corpus_dirname).first()
            if corpus:
                try:
                    result = corpus.index()
                    self.stdout.write(f'Corpus {corpus.slug}\n')
                except Exception as e:
                    self.stdout.write(f'Error indexing corpus {corpus.slug}\n')
                    self.stdout.write(f'{e}\n')
            else:
                self.stdout.write('No matching corpus found.\n')
        