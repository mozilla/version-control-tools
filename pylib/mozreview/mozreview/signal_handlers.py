from __future__ import unicode_literals

from django.db.models.signals import (
    post_save,
)

from reviewboard.extensions.hooks import (
    SignalHook,
)
from reviewboard.reviews.models import (
    ReviewRequestDraft,
)

from mozreview.extra_data import (
    get_parent_rr,
    is_parent,
    is_pushed,
    update_parent_rr_reviewers
)


def initialize_signal_handlers(extension):
    """Initialize signal handlers.

    Any initialization of the signal handlers, including instantiating
    SignalHooks should take place inside this function. An extension
    should call it during initialize().
    """
    SignalHook(
        extension,
        post_save,
        ensure_parent_draft,
        sender=ReviewRequestDraft)


def ensure_parent_draft(sender, **kwargs):
    """Ensure parent draft exists when child has a draft.

    This is intended to handle the post_save signal for the
    ReviewRequestDraft model and ensure the parent review request
    has a draft if a child draft is saved. We need to do this so
    that the parent may always be published when a child requires
    publishing.

    Particularly we update our own reviewer information in the
    parent to make sure that a reviewer change on a child request
    will create a parent draft - even if the reviewer change does
    not alter the overall set of reviewers for the series.
    """
    instance = kwargs["instance"]
    rr = instance.get_review_request()

    if is_pushed(instance) and not is_parent(rr):
        parent_rr = get_parent_rr(rr)
        parent_rr_draft = parent_rr.get_draft()

        if parent_rr_draft is None:
            parent_rr_draft = ReviewRequestDraft.create(parent_rr)

        update_parent_rr_reviewers(parent_rr_draft)
