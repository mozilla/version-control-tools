from __future__ import unicode_literals

from djblets.webapi.errors import WebAPIError


BAD_AUTOLAND_URL = WebAPIError(
    900,
    "Autoland has not been configured with a proper URL endpoint.",
    http_status=500)  # 500 Internal Server Error

AUTOLAND_ERROR = WebAPIError(
    901,
    "Autoland returned an error message during communications.",
    http_status=502)  # 502 Bad Gateway

AUTOLAND_TIMEOUT = WebAPIError(
    902,
    "Autoland failed to respond within the allowed time",
    http_status=502)  # 502 Bad Gateway

BAD_AUTOLAND_CREDENTIALS = WebAPIError(
    903,
    "Bad or missing Autoland credentials.",
    http_status=401)  # 401 Unauthorized
