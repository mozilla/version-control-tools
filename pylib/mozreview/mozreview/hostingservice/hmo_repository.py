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

    landing_repository_url = forms.CharField(
        label=_('Autoland Repository URL'),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'size': '60'}),
        help_text=_('URL for repository to land completed work (if any)'))

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
            'landing_repository_url': '%(landing_repository_url)s',
            'required_ldap_group': '%(required_ldap_group)s',
        },
    }

    def check_repository(self, *args, **kwargs):
        return True

    def is_authorized(self):
        return True

    # This needs to be overridden here because the version defined in
    # HostingService drops kwargs which causes the base_commit_id to be lost,
    # which in turns causes the tip revision to always be retrieved, breaking
    # diffs. To be safe, we also override get_file_exists which could also be
    # affected by this. See Bug 1208213.
    def get_file(self, repository, path, revision, *args, **kwargs):
        return repository.get_scmtool().get_file(path, revision, **kwargs)

    def get_file_exists(self, repository, path, revision, *args, **kwargs):
        return repository.get_scmtool().file_exists(path, revision, **kwargs)
