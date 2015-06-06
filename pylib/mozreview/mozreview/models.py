from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

from mozreview.autoland.models import (AutolandEventLogEntry,
                                       AutolandRequest)
from mozreview.bugzilla.models import (BugzillaUserMap,
                                       get_or_create_bugzilla_users,
                                       set_bugzilla_api_key,
                                       UnverifiedBugzillaApiKey)
from mozreview.ldap import query_scm_group

__all__ = [
    'AutolandEventLogEntry',
    'AutolandRequest',
    'BugzillaUserMap',
    'get_or_create_bugzilla_users',
    'MozReviewUserProfile',
    'set_bugzilla_api_key',
    'UnverifiedBugzillaApiKey',
]


def get_profile(user):
    """Return the MozReviewUserProfile associated with a user.

    If the MozReviewUserProfile object does not exist a default
    one will be created.
    """
    return MozReviewUserProfile.objects.get_or_create(user=user)[0]


class MozReviewUserProfile(models.Model):
    """Extra User Profile information for MozReview"""
    user = models.OneToOneField(User, primary_key=True)

    # ldap username associated with the user. Blank indicates
    # the RB user has not yet been associated with an ldap account.
    # A non blank value indicates the user has proven they control
    # that ldap username and should be given the permissions
    # associated with its groups in ldap.
    ldap_username = models.CharField(max_length=256, blank=True)

    def has_scm_ldap_group(self, group):
        """Return True if the user is a member of the provided ldap group."""
        if not self.ldap_username:
            return False

        return query_scm_group(self.ldap_username, group)


    class Meta:
        app_label = 'mozreview'
        permissions = (
            ("modify_ldap_association",
             "Can change ldap assocation for all users"),
        )
