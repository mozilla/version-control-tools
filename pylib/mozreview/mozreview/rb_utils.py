from __future__ import unicode_literals

from django.contrib.sites.models import (
    Site,
)

from djblets.siteconfig.models import (
    SiteConfiguration,
)
from reviewboard.site.urlresolvers import (
    local_site_reverse,
)


def get_obj_url(obj, site=None, siteconfig=None):
    if not site:
        site = Site.objects.get_current()

    if not siteconfig:
        siteconfig = SiteConfiguration.objects.get_current()

    return '%s://%s%s%s' % (
        siteconfig.get('site_domain_method'), site.domain,
        local_site_reverse('root').rstrip('/'),
        obj.get_absolute_url())
