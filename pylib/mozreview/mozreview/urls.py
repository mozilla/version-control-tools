from __future__ import unicode_literals

from django.conf.urls import patterns, url
from django.contrib.auth import views as auth_views


urlpatterns = patterns(
    'mozreview.views',

    # authentication
    url(r'^login/$', 'bmo_login', name='bmo-login'),
    url(r'^bmo_auth_callback/$', 'bmo_auth_callback',
        name='bmo-auth-callback'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/r/'}),

    # reviews
    url(r'^commits_summary_table/(?P<parent_id>[0-9]+)/(?P<child_id>[0-9]+)/$',
        'commits_summary_table_fragment'),
)
