from django.core.management.base import BaseCommand, CommandError
from gh_ingest.scraper import GithubCorpusScraper, LocalCorpusScraper
from gh_ingest.scraper_exceptions import ScraperException
from gh_ingest.htmlvis import HtmlGenerationException
from django.conf import settings


class Command(BaseCommand):
	help = 'Use to ingest corpus data from GitHub or local directory'

	def add_arguments(self, parser):
		parser.add_argument(
			'corpus_dirnames',
			nargs='+',
			type=str,
			help="The name of a top-level directory inside of the corpus GitHub repository"
		)
		parser.add_argument(
			'--source',
			choices=['github', 'local'],
			default='github',
			help="Specify the source of the corpus data. Options are 'github' or 'local'. Default is 'github'."
		)
		parser.add_argument(
			'--local-repo-path',
			type=str,
			help="Specify the local repository path when using --source local."
		)

	def handle(self, *args, **options):
		if options['source'] == 'github':
			scraper = GithubCorpusScraper()
		else:
			if not options['local_repo_path']:
				raise CommandError("The --local-repo-path argument is required when --source is 'local'.")
			settings.LOCAL_REPO_PATH = options['local_repo_path']
			scraper = LocalCorpusScraper()

		try:
			transactions = scraper.parse_corpora(options['corpus_dirnames'])
		except (ScraperException, HtmlGenerationException) as e:
			raise CommandError(e) from e

		for transaction in transactions:
			self.stdout.write(f"Prepared transaction for corpus {transaction.corpus_name}. Executing...")
			try:
				counts = transaction.execute()
			except Exception as e:
				self.stdout.write(self.style.ERROR("Something went wrong while attempting to execute the transaction "
												   f"for corpus '{transaction.corpus_name}'. No changes have been "
												   f"committed for corpus '{transaction.corpus_name}'.\nError details: "))
				raise e

			self.stdout.write(self.style.SUCCESS(f"Successfully ingested corpus '{transaction.corpus_name}' with"
												 f" {counts['texts']} texts,"
												 f" {counts['vises']} visualizations,"
												 f" and {counts['text_metas']} pieces of metadata"))

		# TODO: would be nice to prompt the user for human-readable names
		self.stdout.write("Your next step should be to enter the admin interface and give each "
						  "corpus a human-readable name and an appropriate URN code.")
