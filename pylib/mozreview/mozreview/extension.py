from reviewboard.extensions.base import Extension

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
    }

    is_configurable = True

    def initialize(self):
        initialize_pulse_handlers(self)
