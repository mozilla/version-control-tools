import logging

from django import forms
from django.utils.translation import ugettext_lazy as _

from reviewboard.hostingsvcs.forms import HostingServiceForm
from reviewboard.hostingsvcs.service import HostingService


class HMORepositoryForm(HostingServiceForm):
    repository_url = forms.CharField(
        label=_('Repository URL'),
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'size': '60'}),
        help_text=_('Canonical url for repository'))

    try_repository_url = forms.CharField(
        label=_('Try Repository URL'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'size': '60'}),
        help_text=_('URL for associated Try repository (if any)'))

    required_ldap_group = forms.CharField(
        label=_('Required LDAP group'),
        # Default to a restrictive group just to be safe.
        initial='scm_level_3',
        required=False,
        help_text=_('LDAP group membership required to push to this '
                    'repository'))


class HMORepository(HostingService):
    name = 'hmo'

    supports_repositories = True
    form = HMORepositoryForm
    supported_scmtools = ['Mercurial']
    repository_fields = {
        'Mercurial': {
            'path': '%(repository_url)s',
            'try_repository_url': '%(try_repository_url)s',
            'required_ldap_group': '%(required_ldap_group)s',
        },
    }

    def check_repository(self, *args, **kwargs):
        return True

    def is_authorized(self):
        return True
