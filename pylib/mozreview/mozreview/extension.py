from __future__ import unicode_literals

from djblets.webapi.resources import (register_resource_for_model,
                                      unregister_resource_for_model)
from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import HeaderDropdownActionHook

from mozreview.autoland.models import AutolandRequest
from mozreview.autoland.resources import (autoland_request_update_resource,
                                          try_autoland_trigger_resource)
from mozreview.batchreview.resources import batch_review_resource
from mozreview.pulse import initialize_pulse_handlers
from mozreview.resources.review_request_summary import (
    review_request_summary_resource,)


class MozReviewExtension(Extension):
    metadata = {
        'Name': 'mozreview',
        'Summary': 'MozReview extension to Review Board',
    }

    default_settings = {
        'enabled': False,
        'pulse_host': '',
        'pulse_port': '',
        'pulse_user': '',
        'pulse_password': '',
        'pulse_ssl': False,
        'autoland_url': '',
        'autoland_user': '',
        'autoland_password': '',
        'autoland_testing': False,
    }

    is_configurable = True

    resources = [
        autoland_request_update_resource,
        batch_review_resource,
        review_request_summary_resource,
        try_autoland_trigger_resource,
    ]

    def initialize(self):
        register_resource_for_model(AutolandRequest,
                                    try_autoland_trigger_resource)
        initialize_pulse_handlers(self)

        HeaderDropdownActionHook(self, actions=[{
            'label': 'MozReview',
            'items': [
                {
                    'label': 'User Guide',
                    'url': 'https://mozilla-version-control-tools.readthedocs.org/en/latest/mozreview-user.html',
                },
                {
                    'label': 'Mercurial for Mozillians',
                    'url': 'https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmozilla/index.html',
                },
                {
                    'label': 'Hacking MozReview',
                    'url': 'https://mozilla-version-control-tools.readthedocs.org/en/latest/hacking-mozreview.html',
                },
                {
                    'label': 'File a Bug',
                    'url': 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=MozReview',
                },
            ],
        }])

    def shutdown(self):
        unregister_resource_for_model(AutolandRequest)
