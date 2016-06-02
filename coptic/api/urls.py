from django.conf.urls import patterns, url
from api import views 

urlpatterns = patterns('',
   url(r'^(?P<params>.*)$', views.api, name='api'),
)