from django.conf.urls import patterns, include, url
from django.contrib import admin


urlpatterns = patterns('',
	url(r'^grappelli/', include('grappelli.urls')),
	url(r'^admin/', include(admin.site.urls)),
	url(r'^api/', include('api.urls')),
	url(r'^texts/', include('texts.urls')),
	url(r'^urn', include('urn.urls')),
	url(r'^collections/.+$', 'coptic.views.home', name='home'),
	url(r'^filter/.+$', 'coptic.views.home', name='home'),
	url(r'^$', 'coptic.views.home', name='home'),
)
