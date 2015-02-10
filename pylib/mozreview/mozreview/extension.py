from __future__ import unicode_literals

from djblets.webapi.resources import (register_resource_for_model,
                                      unregister_resource_for_model)
from reviewboard.extensions.base import Extension

from mozreview.autoland.models import AutolandRequest
from mozreview.autoland.resources import (autoland_request_update_resource,
                                          try_autoland_trigger_resource)
from mozreview.batchreview.resources import batch_review_resource
from mozreview.pulse import initialize_pulse_handlers


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

    resources = [
        batch_review_resource,
    ]

    is_configurable = True

    resources = [
        autoland_request_update_resource,
        try_autoland_trigger_resource,
    ]

    def initialize(self):
        register_resource_for_model(AutolandRequest,
                                    try_autoland_trigger_resource)
        initialize_pulse_handlers(self)

    def shutdown(self):
        unregister_resource_for_model(AutolandRequest)
