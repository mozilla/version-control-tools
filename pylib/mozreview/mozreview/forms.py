from django import forms

from djblets.extensions.forms import SettingsForm


class MozReviewSettingsForm(SettingsForm):
    enabled = forms.BooleanField(initial=False, required=False)
    pulse_host = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'size': 100,
        }))
    pulse_port = forms.IntegerField(required=False)
    pulse_ssl = forms.BooleanField(required=False)
    pulse_user = forms.CharField(required=False)
    pulse_password = forms.CharField(required=False,
                                     widget=forms.PasswordInput)
    autoland_url = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'size': 100,
        }))
    autoland_user = forms.CharField(required=False)
    autoland_password = forms.CharField(required=False,
                                        widget=forms.PasswordInput)

    autoland_testing = forms.BooleanField(initial=False, required=False)
