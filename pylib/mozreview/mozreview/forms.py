from django import forms
from django.utils.translation import ugettext as _
from djblets.extensions.forms import SettingsForm
from djblets.siteconfig.forms import SiteSettingsForm

import mozreview.extension


class MozReviewSettingsForm(SettingsForm):
    config = forms.CharField(
        required=False,
        help_text=_('Configure this extension by editing ' +
                    mozreview.extension.SETTINGS_PATH)
    )


class BugzillaAuthSettingsForm(SiteSettingsForm):
    auth_bz_xmlrpc_url = forms.CharField(
        label="Bugzilla XMLRPC URL",
        help_text="URL for your Bugzilla installation's XMLRPC interface",
        required=True)

    class Meta:
        title = "Bugzilla Backend Settings"
