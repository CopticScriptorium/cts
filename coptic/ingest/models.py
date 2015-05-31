import pdb
import datetime
from django.db import models
from django.forms import ValidationError
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from ingest.expire import expire_ingest 
from ingest.tasks import shared_task_spawn_ingest
import logging


class Ingest(models.Model):
	"""
	Model for creating new ingests of documents and metadata

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

		logger.info(" -- Ingest: Deleting all previous ingests")
		Ingest.objects.all().delete()

		return super(Ingest, self).save(*args, **kwargs)

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

		return super(ExpireIngest, self).save(*args, **kwargs)


# Method for performing ingest
def post_save_ingest(sender, instance, **kwargs):
	result = shared_task_spawn_ingest.delay(instance.id)

# Method for expiring ingest
def post_save_expire_ingest(sender, instance, **kwargs):
	expire_ingest( instance )

# Register the post save signals
post_save.connect(post_save_ingest, sender=Ingest, dispatch_uid="")
post_save.connect(post_save_expire_ingest, sender=ExpireIngest, dispatch_uid="")	