from django.contrib.auth import login
from djblets.webapi.decorators import (webapi_request_fields,
                                       webapi_response_errors)
from djblets.webapi.errors import (INVALID_FORM_DATA,
                                   LOGIN_FAILED,
                                   SERVICE_NOT_CONFIGURED)
from reviewboard.accounts.backends import get_registered_auth_backend
from reviewboard.webapi.decorators import webapi_check_local_site
from reviewboard.webapi.resources import WebAPIResource


class BugzillaCookieLoginResource(WebAPIResource):
    """Resource for authenticating using a bugzilla cookie.

    This resource allows authentication by providing a valid bugzilla
    user id and an associated login cookie. If the Bugzilla authentication
    backend is not enabled we will return an error and not attempt to
    login.
    """
    name = 'bugzilla_cookie_login'
    allowed_methods = ('GET', 'POST',)

    @webapi_check_local_site
    @webapi_response_errors(INVALID_FORM_DATA, LOGIN_FAILED,
                            SERVICE_NOT_CONFIGURED)
    @webapi_request_fields(
        required={
            'login_id': {
                'type': str,
                'description': 'The bugzilla login ID.',
            },
            'login_cookie': {
                'type': str,
                'description': 'The bugzilla login cookie value.',
            },
        }
    )
    def create(self, request, login_id, login_cookie, *args, **kwargs):
        """Authenticate a user using a bugzilla cookie."""
        # The bugzilla auth backend must be enabled to use this
        # resource, so check if it is.
        auth_backend_cls = get_registered_auth_backend('bugzilla')
        if not auth_backend_cls:
            return SERVICE_NOT_CONFIGURED

        bugzilla_backend = auth_backend_cls()
        user = bugzilla_backend.authenticate(login_id, login_cookie,
                                             cookie=True)

        if user is None:
            return LOGIN_FAILED

        user.backend = 'rbbz.auth.BugzillaBackend'

        # Authentication succeeded, persist the returned user for
        # the session.
        login(request, user)

        # It might make sense to return more data about the result of a
        # successful login but for now we'll just return the email address
        # of the user.
        return 201, {
            self.item_result_key: {
                'email': user.email,
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


bugzilla_cookie_login_resource = BugzillaCookieLoginResource()
