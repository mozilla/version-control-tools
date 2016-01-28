from __future__ import unicode_literals

from django.conf.urls import patterns, url
from django.contrib.auth import views as auth_views


urlpatterns = patterns(
    'mozreview.views',

    url(r'^bmo_auth_callback/$', 'bmo_auth_callback',
        name='bmo-auth-callback'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/r/'}),
)
