from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from reviewboard.diffviewer.models import (
    DiffSet,
)


# It is fine to use real foreign keys in our extension
# as long as we do not attempt to access the relationship
# backwards from a built-in model. For context, see
# https://reviews.reviewboard.org/r/6224/


class DiffSetVerification(models.Model):
    """Verification that a DiffSet was uploaded to RB by the hg server."""
    diffset = models.OneToOneField(
        DiffSet,
        primary_key=True,
        help_text=_('The DiffSet which is verified by this object. We should '
                    'never allow a DiffSet to be published without making '
                    'sure it is verified (this object exists). If a DiffSet '
                    'does not have a corresponding verification, it was not '
                    'uploaded by a user with the `verify_diffset` '
                    'permission.'))

    class Meta:
        app_label = 'mozreview'
        permissions = (
            ('verify_diffset', 'Can verify DiffSet legitimacy'),
        )
