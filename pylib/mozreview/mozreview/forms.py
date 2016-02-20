from django import forms
from django.utils.translation import ugettext as _
from djblets.extensions.forms import SettingsForm

import mozreview.extension


class MozReviewSettingsForm(SettingsForm):
    config = forms.CharField(
        required=False,
        help_text=_('Configure this extension by editing ' +
                    mozreview.extension.SETTINGS_PATH)
    )
