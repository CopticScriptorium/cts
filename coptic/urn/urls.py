from django.conf.urls import patterns, url
from urn import views


urlpatterns = patterns('',

    # urn redirect 
    url(r'^(.+)$', views.urn_redirect, name='redirect'),

)