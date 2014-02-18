# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from reviewboard.extensions.base import Extension
from rbbz.forms import BugzillaAuthSettingsForm
from rbbz.middleware import BugzillaCookieAuthMiddleware


class BugzillaExtension(Extension):
    middleware = [BugzillaCookieAuthMiddleware]
    settings_form = BugzillaAuthSettingsForm
