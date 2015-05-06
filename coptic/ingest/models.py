
import datetime
from django.db import models
from django.forms import ValidationError
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from ingest.ingest import fetch_texts


class Ingest(models.Model):
	"""
	Class for creating new ingests of documents

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
		Ingest.objects.all().delete()

		return super(Ingest, self).save(*args, **kwargs)


# Method for performing ingest once there's an ingest.id 
def post_save_ingest(sender, instance, **kwargs):
	fetch_texts( instance )

# Register the post save signal 
post_save.connect(post_save_ingest, sender=Ingest, dispatch_uid="")	