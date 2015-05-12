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


NOT_PUSHED_PARENT_REVIEW_REQUEST = WebAPIError(
    800,
    'This operation must be performed on the parent of a pushed review '
    'request.',
    http_status=405)  # 405 Method Not Allowed
