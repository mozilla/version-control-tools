from reviewboard.extensions.base import Extension

from mozreview.pulse import initialize_pulse_handlers


class MozReviewExtension(Extension):
    metadata = {
        'Name': 'mozreview',
        'Summary': 'MozReview extension to Review Board',
    }

    def initialize(self):
        initialize_pulse_handlers(self)
