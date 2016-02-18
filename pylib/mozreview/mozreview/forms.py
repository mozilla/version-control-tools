from django import forms
from django.contrib import messages
from django.utils.translation import ugettext as _
from djblets.extensions.forms import SettingsForm

from reviewboard.accounts.forms.pages import AccountPageForm

import mozreview.extension


class MozReviewSettingsForm(SettingsForm):
    config = forms.CharField(
        required=False,
        help_text=_('Configure this extension by editing ' +
                    mozreview.extension.SETTINGS_PATH)
    )


class MozReviewAccountSettingsForm(AccountPageForm):
    form_id = 'mozreview_accountsettings_page'
    extra_data_key = 'mozreview_dblclick_comment'
    form_title = 'Additional MozReview Customizations'
    default = True

    mozreview_dblclick_comment = forms.BooleanField(
        label=_('Double-clicking a line number should start a comment'),
        help_text=_('This is similar to how Bugzilla Splinter behaves'),
        initial=True,
        required=False)

    def load(self):
        """Loads in data for the Account Settings form"""
        current = self.default
        if self.extra_data_key in self.profile.extra_data:
            current = self.profile.extra_data[self.extra_data_key]

        self.set_initial({
            self.extra_data_key: current,
        })

    def save(self):
        """Save data for the Account Settings form"""
        cleaned = self.cleaned_data[self.extra_data_key]
        self.profile.extra_data[self.extra_data_key] = cleaned
        self.profile.save(update_fields=('extra_data',))

        messages.add_message(self.request, messages.INFO,
                             _('Your settings have been saved.'))