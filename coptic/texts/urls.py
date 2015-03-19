from django.conf.urls import patterns, url
from texts import views

urlpatterns = patterns('',

	# list/index
    url(r'^$', views.list, name='list'),

    # single - Let the client side take care
    # url(r'^(?P<slug>.+)/$', views.single, name='single'),
    url(r'^(?P<slug>.+)$', views.list, name='single'),


)