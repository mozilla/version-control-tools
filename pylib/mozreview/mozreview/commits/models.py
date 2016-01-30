from __future__ import unicode_literals

from django.core.exceptions import (
    PermissionDenied,
)
from django.db import (
    models,
)
from django.utils.translation import (
    ugettext_lazy as _,
)

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

    def save(self, authorized_user=None, *args, **kwargs):
        """Save the DiffSetVerification.

        We require a User with the `verify_diffset` permission to be passed
        to save to prevent accidental verifications of a DiffSet in any
        code added in the future.
        """
        if authorized_user is None:
            raise PermissionDenied(
                'A DiffsetVerification may not be saved without providing a '
                'User object with the verify_diffset permission.')
        elif not authorized_user.has_perm('mozreview.verify_diffset'):
            raise PermissionDenied(
                'Provided User does not have permission to verify a DiffSet.')

        super(DiffSetVerification, self).save(*args, **kwargs)

    class Meta:
        app_label = 'mozreview'
        permissions = (
            ('verify_diffset', 'Can verify DiffSet legitimacy'),
        )
