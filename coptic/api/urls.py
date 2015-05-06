from django.conf.urls import patterns, url
from api import views 


urlpatterns = patterns('',

    # Api query, send to api for json_view module 
    url(r'^.*$', views.api, name='api'),


)