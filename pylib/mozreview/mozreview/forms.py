from django import forms
from django.utils.translation import ugettext as _
from djblets.extensions.forms import SettingsForm


class MozReviewSettingsForm(SettingsForm):
    enabled = forms.BooleanField(
        initial=False,
        required=False,
        label=_('Enable Pulse'))
    pulse_host = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'size': 100,
        }))
    pulse_port = forms.IntegerField(required=False)
    pulse_ssl = forms.BooleanField(required=False)
    pulse_user = forms.CharField(required=False)
    pulse_password = forms.CharField(required=False,
                                     widget=forms.PasswordInput(
                                        render_value=True))
    autoland_import_pullrequest_ui_enabled = forms.BooleanField(
        label=_('Enable Autoland Import Pullrequest UI'),
        help_text=_('This allows access to the web endpoint for importing '
                    'Github pull requests'),
        initial=False,
        required=False)
    autoland_try_ui_enabled = forms.BooleanField(
        label=_('Enable Autoland Try UI'),
        help_text=_('This exposes the field in a push-based review request '
                    'for scheduling Try Autoland jobs'),
        initial=False,
        required=False)
    autoland_url = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'size': 100,
        }))
    autoland_user = forms.CharField(required=False)
    autoland_password = forms.CharField(required=False,
                                        widget=forms.PasswordInput(
                                            render_value=True))
    autoland_testing = forms.BooleanField(initial=False, required=False)
    ldap_url = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'size': 100,
        }))
    ldap_user = forms.CharField(required=False)
    ldap_password = forms.CharField(required=False,
                                    widget=forms.PasswordInput(
                                        render_value=True))
