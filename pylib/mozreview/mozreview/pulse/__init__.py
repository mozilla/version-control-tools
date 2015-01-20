from reviewboard.extensions.hooks import SignalHook
from reviewboard.reviews.signals import review_request_published

from mozillapulse import publishers
from mozillapulse.messages import base

from mozreview.decorators import if_ext_enabled


def initialize_pulse_handlers(extension):
    SignalHook(extension, review_request_published,
               handle_review_request_published)


@if_ext_enabled
def handle_review_request_published(extension=None, **kwargs):
    review_request = kwargs.get('review_request')

    # TODO: Expand this message to make it useful
    msg = base.GenericMessage()
    msg.routing_parts.append('mozreview.review_request.published')
    msg.data['id'] = review_request.id

    publish_message(extension, msg)

def publish_message(extension, msg):
    config = get_pulse_config(extension)
    pulse = publishers.MozReviewPublisher(**config)

    try:
        pulse.publish(msg)
    finally:
        pulse.disconnect()

def get_pulse_config(extension):
    return {
        'host': extension.settings['pulse_host'] or None,
        'user': extension.settings['pulse_user'] or None,
        'password': extension.settings['pulse_password'] or None,
    }
