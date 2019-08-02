from django.conf.urls import url
from api import views 

# django <= 1.7
try:
   from django.conf.urls import patterns
   urlpatterns = patterns('',
      url(r'^(?P<params>.*)$', views.api, name='api'),
   )
except ImportError:
   urlpatterns = [
      url(r'^(?P<params>.*)$', views.api, name='api')
   ]
