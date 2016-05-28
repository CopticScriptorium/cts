from django.conf.urls import patterns, url
from api import views 

urlpatterns = patterns('',
   url(r'^search', views.search, name='search'),
   url(r'^(?P<params>.*)$', views.api, name='api'),
)