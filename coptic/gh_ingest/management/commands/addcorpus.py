from django.core.management.base import BaseCommand, CommandError
from gh_ingest.scraper import GithubCorpusScraper, ScraperException


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
			transactions = scraper.parse_corpora(options['corpus_dirnames'])
		except ScraperException as e:
			raise CommandError(e) from e


		for transaction in transactions:
			self.stdout.write(f"Prepared Django model objects for corpus {transaction.corpus_name}. "
							  f"Executing transaction...")
			try:
				counts = transaction.execute()
			except Exception as e:
				self.stdout.write(self.style.ERROR("Something went wrong while attempting to execute the transaction. No "
												   "changes have been committed.\nError details: "))
				raise e

			self.stdout.write(self.style.SUCCESS(f"Successfully ingested "
												 f"{counts['texts']} texts "
												 f"and {counts['text_metas']} pieces of metadata"
												 f" for corpus {transaction.corpus_name}."))

		self.stdout.write("Hello, world!")



