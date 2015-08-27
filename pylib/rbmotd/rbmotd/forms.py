import hashlib

from django import forms
from django.utils.translation import ugettext as _

from djblets.extensions.forms import SettingsForm


class MotdSettingsForm(SettingsForm):
    enabled = forms.BooleanField(initial=False, required=False)
    message = forms.CharField(
        max_length=512,
        required=False,
        help_text=_('This field expects valid HTML. Entities must be '
                    'properly escaped.'),
        widget=forms.TextInput(attrs={
            'size': 100,
        }))

    def save(self):
        if not self.errors:
            self.siteconfig.set(
                'message_id',
                hashlib.sha256(self.cleaned_data['message']).hexdigest())

        super(MotdSettingsForm, self).save()
