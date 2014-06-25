from django.conf.urls import patterns, url


urlpatterns = patterns('rbmozui.views',
    url(r'^commits/(?P<review_request_id>[0-9]+)/$', 'commits', name='rbmozui-commits')
)
