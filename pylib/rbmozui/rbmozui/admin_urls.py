from __future__ import unicode_literals

from django.conf.urls import patterns, url

from rbmozui.extension import RBMozUI


urlpatterns = patterns(
    'rbmozui.views',

    url(r'^$', 'configure'),
)