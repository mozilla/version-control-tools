import posixpath

from urllib import urlencode
from urlparse import urljoin, urlparse, urlunparse

from django import template
from django.core.urlresolvers import reverse

from djblets.siteconfig.models import SiteConfiguration


register = template.Library()


@register.simple_tag(takes_context=True)
def bugzilla_auth_uri(context):
    # TODO: We only store the XML-RPC URL in our settings, but we need
    # the auth URL.  Ideally we'd store just the root Bugzilla URL
    # and modify it where appropriate, but we'll be switching to REST at
    # some point so we might as well fix it then.
    request = context['request']
    redirect = request.GET.get('next')
    callback_uri = request.build_absolute_uri(reverse('bmo-auth-callback'))

    if redirect:
        callback_uri += '?%s' % urlencode({'redirect': redirect})

    siteconfig = SiteConfiguration.objects.get_current()
    xmlrpc_url = siteconfig.get('auth_bz_xmlrpc_url')
    u = urlparse(xmlrpc_url)
    bugzilla_root = posixpath.dirname(u.path).rstrip('/') + '/'
    query_dict = {'description': 'mozreview', 'callback': callback_uri}

    return urlunparse((u.scheme, u.netloc, urljoin(bugzilla_root, 'auth.cgi'),
                       '', urlencode(query_dict), ''))


@register.assignment_tag(takes_context=True)
def get_full(context):
    request = context['request']
    return bool(request.GET.get('full'))
