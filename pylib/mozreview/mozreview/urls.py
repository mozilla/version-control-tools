from __future__ import unicode_literals

from django.conf.urls import patterns, url


urlpatterns = patterns('mozreview.views',
    url(r'^bmo_auth_callback/$', 'bmo_auth_callback', name='bmo-auth-callback'),
)
