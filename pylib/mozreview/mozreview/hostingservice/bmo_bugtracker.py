from __future__ import unicode_literals

import logging

from django import forms
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from reviewboard.admin.validation import validate_bug_tracker_base_hosting_url
from reviewboard.hostingsvcs.bugtracker import BugTracker
from reviewboard.hostingsvcs.forms import HostingServiceForm
from reviewboard.hostingsvcs.service import HostingService


class BMOForm(HostingServiceForm):
    bmo_url = forms.CharField(
        label=_('Bugzilla URL'),
        max_length=64,
        required=True,
        widget=forms.TextInput(attrs={'size': '60'}),
        validators=[validate_bug_tracker_base_hosting_url])

    def clean_bmo_url(self):
        return self.cleaned_data['bmo_url'].rstrip('/')


class BMOBugTracker(HostingService, BugTracker):
    name = 'BMO'
    form = BMOForm
    bug_tracker_field = '%(bmo_url)s/show_bug.cgi?id=%%s'
    supports_bug_trackers = True

    def get_bug_info_uncached(self, repository, bug_id):
        """Get the bug info from the server."""
        bug_id = six.text_type(bug_id)

        result = {
            'summary': '',
            'description': '',
            'status': '',
        }

        try:
            # TODO investigate if it makes more sense to display BMO's
            # user-story field, if set, instead of the description.
            url = '%s/rest/bug/%s?include_fields=summary,status,resolution' % (
                repository.extra_data['bug_tracker-bmo_url'], bug_id)
            rsp, headers = self.client.json_get(url)
            result['summary'] = str(rsp['bugs'][0]['summary'])
            result['status'] = str(rsp['bugs'][0]['status'])
            if result['status'] == 'RESOLVED':
                result['status'] += ' ' + rsp['bugs'][0]['resolution']
        except Exception as e:
            logging.warning('Unable to fetch BMO data from %s: %s',
                            url, e, exc_info=1)

        try:
            url = '%s/rest/bug/%s/comment?include_fields=text' % (
                repository.extra_data['bug_tracker-bmo_url'], bug_id)
            rsp, headers = self.client.json_get(url)
            result['description'] = str(rsp['bugs'][bug_id]['comments'][0][
                'text'])
        except Exception as e:
            logging.warning('Unable to fetch BMO data from %s: %s',
                            url, e, exc_info=1)

        return result
