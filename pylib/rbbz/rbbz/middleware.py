# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.conf import settings


class CorsHeaderMiddleware(object):
    """Add a CORS header if running in debug mode."""

    def process_response(self, request, response):
        if settings.DEBUG:
            response['Access-Control-Allow-Origin'] = '*'
        return response
