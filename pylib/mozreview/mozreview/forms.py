from django import forms
from django.utils.translation import ugettext as _

from djblets.extensions.forms import SettingsForm


class MozReviewSettingsForm(SettingsForm):
    enabled = forms.BooleanField(initial=False, required=False)
    pulse_host = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'size': 100,
        }))
    pulse_user = forms.CharField(required=False)
    pulse_password = forms.CharField(required=False, widget=forms.PasswordInput)

