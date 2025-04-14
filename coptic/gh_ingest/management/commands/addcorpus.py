from django.core.management.base import BaseCommand, CommandError
from gh_ingest.corpus_scraper import CorpusScraper
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
            help="The names of a top-level directory inside of the corpus GitHub repository"
        )
        parser.add_argument(
            '--local-repo-path',
            type=str,
            help="Specify the local repository path when using --source local."
        )

    def handle(self, *args, **options):
        self.stdout.write("Using Local repo as the source of the corpus data.")
        if not options['local_repo_path']:
            raise CommandError("The --local-repo-path argument is required")
        settings.LOCAL_REPO_PATH = options['local_repo_path']
        
        # Initialize CorpusScraper once
        scraper = CorpusScraper()

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
