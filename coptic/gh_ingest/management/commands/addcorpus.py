from django.core.management.base import BaseCommand, CommandError
from gh_ingest.scraper import GithubCorpusScraper, CorpusNotFound
from gh_ingest.ingest import ingest_corpora


class Command(BaseCommand):
	help = 'Use to '

	def add_arguments(self, parser):
		parser.add_argument('corpora', nargs='+', type=str)

	def handle(self, *args, **options):
		scraper = GithubCorpusScraper()

		try:
			scraper.parse_corpora(options['corpora'])
		except CorpusNotFound as e:
			url = f"https://github.com/{e.repo}/tree/master"
			raise CommandError(f"Could not find corpus '{e.corpus_name}' in {e.repo}."
							   f"\n\tCheck {url} to make sure you spelled it correctly.")

		ingest_corpora(options['corpora'])

		self.stdout.write("Hello, world!")



