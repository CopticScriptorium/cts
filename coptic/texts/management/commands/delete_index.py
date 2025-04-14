from django.core.management.base import BaseCommand
from texts.ft_search import Search

class Command(BaseCommand):
    help = 'Delete Full Text Index'

    def handle(self, *args, **kwargs):
        search = Search()
        if search.search_available:
            search.delete_index()
            self.stdout.write('Index deleted\n')