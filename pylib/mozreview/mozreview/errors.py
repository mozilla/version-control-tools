from __future__ import unicode_literals

from djblets.webapi.errors import WebAPIError

from reviewboard.reviews.errors import PublishError


class CommitPublishProhibited(PublishError):
    def __init__(self):
        PublishError.__init__(self,
                              'Publishing commit review requests is '
                              'prohibited, please publish parent.')


class ParentShipItError(PublishError):
    def __init__(self):
        PublishError.__init__(self, '"Ship it" reviews on parent review '
                              'requests are not allowed.  Please review '
                              'individual commits.')

NOT_PARENT = WebAPIError(
    1001,
    "Review request is not a parent",
    http_status=400)  # 400 Bad Request

CHILD_DOES_NOT_EXIST = WebAPIError(
    1002,
    "Child review request does not exist",
    http_status=500)  # 500 Internal Server Error

class WebLoginNeededError(Exception):
    """Raised when a request requires the user to log in via the web site."""


class BugzillaAPIKeyNeededError(Exception):
    """User should visit Bugzilla to obtain an API key."""
    def __init__(self, url):
        self.url = url


NOT_PUSHED_PARENT_REVIEW_REQUEST = WebAPIError(
    1003,
    'This operation must be performed on the parent of a pushed review '
    'request.',
    http_status=405)  # 405 Method Not Allowed

AUTOLAND_CONFIGURATION_ERROR = WebAPIError(
    1004,
    "Autoland has not been configured with a proper URL endpoint.",
    http_status=500)  # 500 Internal Server Error

AUTOLAND_ERROR = WebAPIError(
    1005,
    "Autoland returned an error message during communications.",
    http_status=502)  # 502 Bad Gateway

AUTOLAND_TIMEOUT = WebAPIError(
    1006,
    "Autoland failed to respond within the allowed time",
    http_status=504)  # 504 Gateway Timeout

AUTOLAND_REQUEST_IN_PROGRESS = WebAPIError(
    1007,
    "An autoland request for this review request is already in progress. "
    "Please wait for that request to finish.",
    http_status=405)  # 405 Method Not Allowed
