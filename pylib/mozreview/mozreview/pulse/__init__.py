from reviewboard.extensions.hooks import SignalHook
from reviewboard.reviews.signals import review_request_published


def initialize_pulse_handlers(extension):
    SignalHook(extension, review_request_published,
               handle_review_request_published)


def handle_review_request_published(**kwargs):
    review_request = kwargs.get('review_request')
