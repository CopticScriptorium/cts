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
	# reinstate the 404 error page after wrapping up primary development
	# url(r'^.+$', 'coptic.views.not_found', name='not_found'),
	url(r'^$', 'coptic.views.home', name='home'),
)
