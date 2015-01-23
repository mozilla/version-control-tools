from django import forms
from django.utils.translation import ugettext as _

from djblets.extensions.forms import SettingsForm


class TryAutolandSettingsForm(SettingsForm):
    autoland_try_ui_enabled = forms.BooleanField(
        label=_('Enable Autoland Try UI'),
        help_text=_('This exposes the field in a push-based review request '
                    'for scheduling Try Autoland jobs'),
        initial=False,
        required=False)
