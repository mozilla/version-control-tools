from __future__ import unicode_literals

from mozreview.forms import MozReviewAccountSettingsForm
from reviewboard.accounts.pages import AccountPage


class MozReviewAccountSettingsPage(AccountPage):
    page_id = 'mozreview_accountsettings_page'
    page_title = 'MozReview Customizations'
    form_classes = [MozReviewAccountSettingsForm]
