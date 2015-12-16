# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.auth import login
from django.contrib.auth.models import User
from djblets.webapi.decorators import (
    webapi_request_fields,
    webapi_response_errors,
)
from djblets.siteconfig.models import SiteConfiguration
from djblets.webapi.errors import (
    INVALID_FORM_DATA,
    LOGIN_FAILED,
    SERVICE_NOT_CONFIGURED,
)
from djblets.webapi.responses import WebAPIResponseError

from reviewboard.accounts.backends import get_registered_auth_backend
from reviewboard.webapi.decorators import webapi_check_local_site
from reviewboard.webapi.resources import WebAPIResource

from mozreview.errors import (
    BugzillaAPIKeyNeededError,
    WebLoginNeededError,
)


def auth_api_key(request, username, api_key):
    """Attempt to authenticate an API key.

    Will return either the User associated with the API key
    or a WebAPIResponseError which should be sent to the
    client.
    """
    backend_cls = get_registered_auth_backend('bugzilla')
    if not backend_cls:
        return SERVICE_NOT_CONFIGURED

    backend = backend_cls()

    try:
        user = backend.authenticate_api_key(username, api_key)
        if user is None:
            return LOGIN_FAILED

    # The user will need to visit Bugzilla to obtain an API key.
    except BugzillaAPIKeyNeededError as e:
        return WebAPIResponseError(request, LOGIN_FAILED, extra_params={
            'bugzilla_api_key_needed': True,
            'bugzilla_api_key_url': e.url,
        })

    # The user hasn't logged in via the HTML interface yet. This
    # error response should be interpretted by clients to direct
    # them to log in to the web site.
    except WebLoginNeededError:
        protocol = SiteConfiguration.objects.get_current().get(
            'site_domain_method')
        domain = Site.objects.get_current().domain
        login_url = '%s://%s%saccount/login' % (
                protocol, domain, settings.SITE_ROOT)

        extra = {
            'web_login_needed': True,
            'login_url': login_url,
        }
        return WebAPIResponseError(request, LOGIN_FAILED,
                                   extra_params=extra)

    # Django housekeeping.
    user.backend = 'rbbz.auth.BugzillaBackend'
    return user


class BugzillaAPIKeyLoginResource(WebAPIResource):
    """Resource for authenticating web API requests from Bugzilla API keys.

    Takes a Bugzilla username and API key and attempts to authenticate.
    """
    name = 'bugzilla_api_key_login'
    allowed_methods = ('GET', 'POST')

    @webapi_check_local_site
    @webapi_response_errors(INVALID_FORM_DATA, LOGIN_FAILED,
                            SERVICE_NOT_CONFIGURED)
    @webapi_request_fields(
        required={
            'username': {
                'type': str,
                'description': 'Bugzilla username/email',
            },
            'api_key': {
                'type': str,
                'description': 'Bugzilla API key',
            }
        }
    )
    def create(self, request, username, api_key, *args, **kwargs):
        """Authenticate a user from a username and API key."""
        backend_cls = get_registered_auth_backend('bugzilla')
        if not backend_cls:
            return SERVICE_NOT_CONFIGURED

        backend = backend_cls()

        try:
            user = backend.authenticate_api_key(username, api_key)
            if user is None:
                return LOGIN_FAILED

        # The user will need to visit Bugzilla to obtain an API key.
        except BugzillaAPIKeyNeededError as e:
            return WebAPIResponseError(request, LOGIN_FAILED, extra_params={
                'bugzilla_api_key_needed': True,
                'bugzilla_api_key_url': e.url,
            })

        # The user hasn't logged in via the HTML interface yet. This
        # error response should be interpretted by clients to direct
        # them to log in to the web site.
        except WebLoginNeededError:
            protocol = SiteConfiguration.objects.get_current().get(
                'site_domain_method')
            domain = Site.objects.get_current().domain
            login_url = '%s://%s%saccount/login' % (
                protocol, domain, settings.SITE_ROOT)

            extra = {
                'web_login_needed': True,
                'login_url': login_url,
            }
        result = auth_api_key(request, username, api_key)

        if not isinstance(result, User):
            return result

        # Authentication succeeded. Persist the returned user for the
        # session.
        login(request, result)

        return 201, {
            self.item_result_key: {
                'email': result.email,
            },
        }

    @webapi_request_fields(allow_unknown=True)
    def get_list(self, request, *args, **kwargs):
        """Handles HTTP GETs to the list resource.

        We override this method to permit accessing the resource anonymously
        even when Review Board is configured to prevent anonymous access.
        This allows using the resource to authenticate with bugzilla without
        already being logged in to the API.
        """
        return 200, {
            'links': self.get_links(self.list_child_resources,
                                    request=request, *args, **kwargs),
        }


bugzilla_api_key_login_resource = BugzillaAPIKeyLoginResource()
