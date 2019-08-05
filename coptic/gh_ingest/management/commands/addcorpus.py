from django.core.management.base import BaseCommand, CommandError
from gh_ingest.scraper import GithubCorpusScraper, CorpusNotFound, EmptyCorpus, AmbiguousCorpus
from gh_ingest.ingest import ingest_corpora


class Command(BaseCommand):
	help = 'Use to '

	def add_arguments(self, parser):
		parser.add_argument(
			'corpus_dirnames',
			nargs='+',
			type=str,
			help="The name of a top-level directory inside of the corpus GitHub repository"
		)

	def handle(self, *args, **options):
		scraper = GithubCorpusScraper()

		try:
			corpora = scraper.parse_corpora(options['corpus_dirnames'])
		except (CorpusNotFound, EmptyCorpus, AmbiguousCorpus) as e:
			raise CommandError(e) from e

		ingest_corpora(corpora)

		self.stdout.write("Hello, world!")



