from __future__ import unicode_literals

from djblets.webapi.errors import WebAPIError


NOT_PUSHED_PARENT_REVIEW_REQUEST = WebAPIError(
    800,
    'This operation must be performed on the parent of a pushed review '
    'request.',
    http_status=405)  # 405 Method Not Allowed
