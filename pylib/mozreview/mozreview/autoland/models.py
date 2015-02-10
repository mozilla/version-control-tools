from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from djblets.db.fields import JSONField


class AutolandRequest(models.Model):
    autoland_id = models.IntegerField(
        primary_key=True,
        help_text=_('The job ID that Autoland returns to us.'))
    push_revision = models.CharField(
        max_length=40,
        help_text=_('The revision ID of the commit that Autoland was asked to '
                    'land.'),
        db_index=True)
    repository_url = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text=_('The URL of the repository that Autoland landed on.'))
    repository_revision = models.CharField(
        max_length=40,
        blank=True,
        default='',
        help_text=_('The revision ID of the commit that Autoland landed.'),
        db_index=True)
    # Unfortunately, Review Board extensions can't take advantage of the
    # ForeignKey ORM magic that Django provides. This is because the extension
    # loading mechanism doesn't do enough (yet) to flush out the foreign key
    # caches in Django.
    review_request_id = models.IntegerField(
        help_text=_('The ID of the review request that Autoland was triggered '
                    'from.'),
        db_index=True)
    user_id = models.IntegerField(
        help_text=_('The ID of the user that triggered the Autoland job.'),
        db_index=True)
    extra_data = JSONField(
        help_text=_('Meta information about this Autoland job.'))

    class Meta:
        app_label = 'mozreview'

    @property
    def last_known_status(self):
        try:
            last_evt = self.event_log_entries.order_by('-pk').all()[0]
            return last_evt.status
        except IndexError:
            # in case we don't have any event yet
            return ""

    @property
    def last_details(self):
        try:
            last_evt = self.event_log_entries.order_by('-pk').all()[0]
            return last_evt.details
        except IndexError:
            return ""


class AutolandEventLogEntry(models.Model):
    REQUESTED = 'R'
    PROBLEM = 'P'
    SERVED = 'S'

    STATUSES = (
        (REQUESTED, _('Request received')),
        (PROBLEM,   _('Problem encountered')),
        (SERVED,    _('Request served')),
    )

    autoland_request = models.ForeignKey(AutolandRequest,
                                         verbose_name=_('autoland_request'),
                                         related_name='event_log_entries')
    event_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(_('status'), max_length=1, choices=STATUSES,
                              db_index=True)
    details = models.TextField(_('details'), blank=True)

    class Meta:
        app_label = 'mozreview'
