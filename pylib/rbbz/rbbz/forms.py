# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django import forms
from djblets.siteconfig.forms import SiteSettingsForm


class BugzillaAuthSettingsForm(SiteSettingsForm):

    auth_bz_xmlrpc_url = forms.CharField(
        label="Bugzilla XMLRPC URL",
        help_text="URL for your Bugzilla installation's XMLRPC interface",
        required=True)

    class Meta:
        title = "Bugzilla Backend Settings"
