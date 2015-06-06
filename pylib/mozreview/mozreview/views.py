from __future__ import unicode_literals

import json
import logging
import uuid

from django.contrib.auth import login
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseNotAllowed)
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from mozreview.bugzilla.client import Bugzilla
from mozreview.bugzilla.errors import BugzillaError
from mozreview.models import (get_or_create_bugzilla_users,
                              set_bugzilla_api_key,
                              UnverifiedBugzillaApiKey)


def show_error_page(request):
    return render_to_response(
        'mozreview/login-error.html', RequestContext(request, {
            'login_error': 'An error occurred when trying to log you in.',
        })
    )


def bmo_auth_callback(request):
    """Callback from Bugzilla for receiving API keys."""
    if request.method == 'GET':
        return get_bmo_auth_callback(request)
    elif request.method == 'POST':
        return post_bmo_auth_callback(request)
    else:
        return HttpResponseNotAllowed(['GET'], ['POST'])


def post_bmo_auth_callback(request):
    """Handler for the first part of the Bugzilla auth-delegation process.

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
        logging.error('Bugzilla auth callback called without required '
                      'parameters.')
        return show_error_page(request)

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
    """Handler for the second part of the Bugzilla auth-delegation process.

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

    if not (bmo_username and callback_result):
        logging.error('Bugzilla auth callback called without required '
                      'parameters.')
        return show_error_page(request)

    if not redirect:
        redirect = '/'

    unverified_keys = UnverifiedBugzillaApiKey.objects.filter(
        bmo_username=bmo_username).order_by('timestamp')

    if not unverified_keys:
        logging.error('No unverified keys found for BMO user %s.' %
                      bmo_username)
        return show_error_page(request)

    unverified_key = unverified_keys.last()

    if len(unverified_keys) > 1:
        logging.warning('Multiple unverified keys on file for BMO user %s. '
                        'Using most recent, from %s.' %
                        (bmo_username, unverified_key.timestamp))

    if callback_result != unverified_key.callback_result:
        logging.error('Callback result does not match for BMO user %s.' %
                      bmo_username)
        return show_error_page(request)

    bmo_api_key = unverified_key.api_key
    unverified_key.delete()

    b = Bugzilla()

    try:
        if not b.valid_api_key(bmo_username, bmo_api_key):
            logging.error('Invalid API key for %s.' % bmo_username)
            return show_error_page(request)
    except BugzillaError as e:
        logging.error('Error validating API key: %s' % e.msg)
        return show_error_page(request)

    b.api_key = bmo_api_key

    try:
        user_data = b.get_user(bmo_username)
    except BugzillaError as e:
        logging.error('Error getting user data: %s' % e.msg)
        return show_error_page(request)

    if not user_data:
        logging.warning('Could not retrieve user info for %s after '
                        'validating API key.' % bmo_username)
        return show_error_page(request)

    users = get_or_create_bugzilla_users(user_data)

    if not users:
        logging.warning('Failed to create user %s after validating API key.' %
                        bmo_username)
        return show_error_page(request)

    user = users[0]
    assert user.email == bmo_username

    if not user.is_active:
        logging.warning('Validated API key but user %s is inactive.' %
                        bmo_username)
        return show_error_page(request)

    set_bugzilla_api_key(user, bmo_api_key)
    user.backend = 'rbbz.auth.BugzillaBackend'
    login(request, user)
    return HttpResponseRedirect(redirect)
