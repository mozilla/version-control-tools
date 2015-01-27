from __future__ import unicode_literals

from djblets.webapi.errors import WebAPIError


NOT_PARENT = WebAPIError(
    1001,
    "Review request is not a parent",
    http_status=400)  # 400 Bad Request

CHILD_DOES_NOT_EXIST = WebAPIError(
    1002,
    "Child review request does not exist",
    http_status=500)  # 500 Internal Server Error
