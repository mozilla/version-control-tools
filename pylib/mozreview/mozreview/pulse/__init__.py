from reviewboard.extensions.hooks import SignalHook
from reviewboard.reviews.signals import review_request_published

from mozreview.decorators import if_ext_enabled


def initialize_pulse_handlers(extension):
    SignalHook(extension, review_request_published,
               handle_review_request_published)


@if_ext_enabled
def handle_review_request_published(extension=None, **kwargs):
    review_request = kwargs.get('review_request')
