from __future__ import unicode_literals

from django.dispatch import Signal


commit_request_publishing = Signal(providing_args=["user",
                                                   "review_request_draft"])
