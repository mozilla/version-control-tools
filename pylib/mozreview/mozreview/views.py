from __future__ import unicode_literals

from datetime import timedelta
import json
import logging
import posixpath
from random import getrandbits
from urllib import urlencode
from urlparse import urljoin, urlparse, urlunparse
import uuid

from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseNotAllowed,
    HttpResponseNotFound,
)
from django.shortcuts import render
from django.utils import timezone

from djblets.siteconfig.models import SiteConfiguration

from mozreview.bugzilla.client import Bugzilla
from mozreview.bugzilla.errors import BugzillaError
from mozreview.ldap import (
    associate_employee_ldap,
    LDAPAssociationException,
)
from mozreview.models import (
    get_or_create_bugzilla_users,
    set_bugzilla_api_key,
    UnverifiedBugzillaApiKey,
)
from mozreview.extra_data import (
    COMMITS_KEY,
    fetch_commit_data,
    is_parent,
    gen_child_rrs,
)
from mozreview.template_helpers import get_commit_table_context

from reviewboard.reviews.models import ReviewRequest


logger = logging.getLogger(__name__)


def render_login_error(request):
    return render(request, 'mozreview/login-error.html', {
        'login_error': 'An error occurred when trying to log you in.',
    })


def bmo_auth_callback(request):
    """Callback from Bugzilla for receiving API keys."""
    if request.method == 'GET':
        return get_bmo_auth_callback(request)
    elif request.method == 'POST':
        return post_bmo_auth_callback(request)
    else:
        return HttpResponseNotAllowed(['GET'], ['POST'])


def bmo_login(request):
    """Handler for the first part of the Bugzilla auth-delegation process.

    Generate a secret, store it in a cookie, and redirect the client
    to Bugzilla.

    The secret will be echoed back to us in a later phase, where is it
    checked aginst the client's cookie to ensure the request and response
    are bound to the same client.
    """
    # TODO: We only store the XML-RPC URL in our settings, but we need
    # the auth URL.  Ideally we'd store just the root Bugzilla URL
    # and modify it where appropriate, but we'll be switching to REST at
    # some point so we might as well fix it then.
    redirect = request.GET.get('next')
    callback_uri = request.build_absolute_uri(reverse('bmo-auth-callback'))
    params = {'secret': '%0x' % getrandbits(16 * 4)}
    if redirect:
        params['redirect'] = redirect
    callback_uri += '?' + urlencode(params)

    siteconfig = SiteConfiguration.objects.get_current()
    xmlrpc_url = siteconfig.get('auth_bz_xmlrpc_url')
    u = urlparse(xmlrpc_url)
    bugzilla_root = posixpath.dirname(u.path).rstrip('/') + '/'
    query_dict = {'description': 'mozreview', 'callback': callback_uri}

    url = urlunparse((u.scheme, u.netloc, urljoin(bugzilla_root, 'auth.cgi'),
                      '', urlencode(query_dict), ''))

    # The bmo_auth_secret is stored in a cookie on the client as well as
    # passed to Bugzilla.  We verify they match when BMO redirects to our
    # callback URI to ensure the request and response are bound to the same
    # client.
    response = HttpResponseRedirect(url)
    response.set_cookie('bmo_auth_secret', params['secret'], max_age=300)
    return response


def post_bmo_auth_callback(request):
    """Handler for the second part of the Bugzilla auth-delegation process.

    After the user is directed to Bugzilla and logs in, Bugzilla sends a
    POST request to this callback with the API key and Bugzilla username.
    This information is stored in the UnverifiedBugzillaApiKey model. This
    handler returns a unique result string to Bugzilla. Bugzilla will then
    redirect the user back to MozReview via a GET request, which contains this
    unique string for validation.
    """
    body = json.loads(request.body)
    bmo_username = body.get('client_api_login', None)
    bmo_api_key = body.get('client_api_key', None)

    if not (bmo_username and bmo_api_key):
        logger.error('Bugzilla auth callback called without required '
                     'parameters.')
        return HttpResponse('Authentication request rejected.',
                            mimetype='text/plain')

    unverified_key = UnverifiedBugzillaApiKey(
        bmo_username=bmo_username,
        api_key=bmo_api_key,
        callback_result=str(uuid.uuid4()))
    unverified_key.save()

    response_data = {'result': unverified_key.callback_result}
    response = HttpResponse(json.dumps(response_data),
                            mimetype="application/json")
    return response


def get_bmo_auth_callback(request):
    """Handler for the third part of the Bugzilla auth-delegation process.

    After the above POST call is executed, Bugzilla then redirects back to
    this view, passing the return value of the POST handler, as
    `callback_result`, and optionally a redirect, passed from the original
    redirect to Bugzilla (from the MozReview login view).

    This handler then verifies the API key with Bugzilla and attempts to
    create or update the user in MozReview.  If everything succeeds, the
    user is again redirected back to the original page (or the root page if
    there was no redirect passed in, e.g., in tests).  Otherwise the user is
    shown an error page.
    """
    bmo_username = request.GET.get('client_api_login', None)
    callback_result = request.GET.get('callback_result', None)
    redirect = request.GET.get('redirect', None)
    secret = request.GET.get('secret', None)

    if not (bmo_username and callback_result):
        logger.error('Bugzilla auth callback called without required '
                     'parameters.')
        return render_login_error(request)

    # Delete expired unverified keys (5 minute lifetime).
    UnverifiedBugzillaApiKey.objects.filter(
        timestamp__lte=timezone.now() - timedelta(minutes=5)).delete()

    parsed = None if not redirect else urlparse(redirect)

    # Enforce relative redirects; we don't want people crafting auth links
    # that redirect to other sites.  We check the scheme as well as the netloc
    # to catch data, file, and other such server-less URIs.

    if not parsed or parsed.scheme or parsed.netloc:
        redirect = '/'

    unverified_keys = UnverifiedBugzillaApiKey.objects.filter(
        bmo_username=bmo_username).order_by('timestamp')

    if not unverified_keys:
        logger.error('No unverified keys found for BMO user %s.' %
                     bmo_username)
        return render_login_error(request)

    unverified_key = unverified_keys.last()

    if len(unverified_keys) > 1:
        logger.warning('Multiple unverified keys on file for BMO user %s. '
                       'Using most recent, from %s.' %
                       (bmo_username, unverified_key.timestamp))

    if callback_result != unverified_key.callback_result:
        logger.error('Callback result does not match for BMO user %s.' %
                     bmo_username)
        return render_login_error(request)

    if secret is None or request.COOKIES['bmo_auth_secret'] != secret:
        logger.error('Callback secret does not match cookie for user %s.' %
                     bmo_username)
        return render_login_error(request)

    bmo_api_key = unverified_key.api_key
    unverified_key.delete()

    b = Bugzilla()

    try:
        if not b.valid_api_key(bmo_username, bmo_api_key):
            logger.error('Invalid API key for %s.' % bmo_username)
            return render_login_error(request)
    except BugzillaError as e:
        logger.error('Error validating API key: %s' % e.msg)
        return render_login_error(request)

    b.api_key = bmo_api_key

    try:
        user_data = b.get_user(bmo_username)
    except BugzillaError as e:
        logger.error('Error getting user data: %s' % e.msg)
        return render_login_error(request)

    if not user_data:
        logger.warning('Could not retrieve user info for %s after '
                       'validating API key.' % bmo_username)
        return render_login_error(request)

    users = get_or_create_bugzilla_users(user_data)

    if not users:
        logger.warning('Failed to create user %s after validating API key.' %
                       bmo_username)
        return render_login_error(request)

    user = users[0]
    assert user.email == bmo_username

    if not user.is_active:
        logger.warning('Validated API key but user %s is inactive.' %
                       bmo_username)
        return render_login_error(request)

    set_bugzilla_api_key(user, bmo_api_key)

    try:
        associate_employee_ldap(user)
    except LDAPAssociationException as e:
        logger.info('LDAP association failed: %s' % str(e))
    except Exception:
        logger.exception('Error while performing LDAP association')

    user.backend = 'mozreview.bugzilla.auth.BugzillaBackend'
    logger.info('BMO Auth callback succeeded for user: %s' % bmo_username)
    login(request, user)
    response = HttpResponseRedirect(redirect)
    response.delete_cookie('bmo_auth_secret')
    return response


def commits_summary_table_fragment(request, parent_id=None, child_id=None):
    """Return the #mozreview-child-requests table."""

    # Load the parent.

    try:
        parent_request = ReviewRequest.objects.get(id=parent_id)
    except ReviewRequest.DoesNotExist:
        return HttpResponseNotFound('Parent Not Found')
    if not parent_request.is_accessible_by(request.user):
        return HttpResponseNotAllowed('Permission denied')

    commit_data = fetch_commit_data(parent_request)

    # Sanity check parent.

    if not is_parent(parent_request, commit_data):
        return HttpResponseNotAllowed('Invalid parent')
    if COMMITS_KEY not in commit_data.extra_data:
        logging.error('Parent review request %s missing COMMITS_KEY'
                      % parent_request.id)
        return HttpResponseNotAllowed('Invalid parent')

    # Load the current child.

    try:
        child_request = ReviewRequest.objects.get(id=child_id)
    except ReviewRequest.DoesNotExist:
        return HttpResponseNotFound('Child Not Found')

    # Sanity check child.

    if is_parent(child_request):
        return HttpResponseNotAllowed('Invalid child')

    # Load all other children and ensure requested child matches parent.

    children_details = list(gen_child_rrs(parent_request, user=request.user))
    if not any(r for r in children_details if r.id == child_request.id):
        return HttpResponseNotAllowed('Invalid child')

    # Return rendered template.

    return render(request, 'mozreview/commits-requests.html',
                  get_commit_table_context(request, child_request))


