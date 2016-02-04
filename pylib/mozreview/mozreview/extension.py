from __future__ import unicode_literals

import json
import logging
import os

from django.conf.urls import include, patterns, url

from reviewboard.extensions.base import Extension, JSExtension
from reviewboard.extensions.hooks import (HeaderDropdownActionHook,
                                          HostingServiceHook,
                                          ReviewRequestDropdownActionHook,
                                          ReviewRequestFieldsHook,
                                          TemplateHook,
                                          URLHook)
from reviewboard.reviews.builtin_fields import (TestingDoneField,
                                                BranchField,
                                                DependsOnField,
                                                BlocksField)
from reviewboard.reviews.fields import (get_review_request_field,
                                        get_review_request_fieldset)
from reviewboard.urls import (diffviewer_url_names,
                              review_request_url_names)

from mozreview.autoland.resources import (
    autoland_request_update_resource,
    autoland_trigger_resource,
    import_pullrequest_trigger_resource,
    import_pullrequest_update_resource,
    try_autoland_trigger_resource,
)
from mozreview.autoland.views import (
    import_pullrequest,
)
from mozreview.batchreview.resources import (
    batch_review_resource,
)
from mozreview.extra_data import (
    is_parent,
)
from mozreview.fields import (
    BaseCommitField,
    CombinedReviewersField,
    CommitsListField,
    FileDiffReviewerField,
    ImportCommitField,
    PullCommitField,
    TryField,
)
from mozreview.file_diff_reviewer.resources import (
    file_diff_reviewer_resource,
)
from mozreview.hooks import (
    MozReviewApprovalHook,
)
from mozreview.hostingservice.hmo_repository import (
    HMORepository,
)
from mozreview.ldap.resources import (
    ldap_association_resource,
)
from mozreview.middleware import (
    MozReviewCacheDisableMiddleware,
    MozReviewUserProfileMiddleware,
)
from mozreview.pulse import (
    initialize_pulse_handlers,
)
from mozreview.resources.bugzilla_login import (
    bugzilla_api_key_login_resource,
)
from mozreview.resources.batch_review_request import (
    batch_review_request_resource,
)
from mozreview.resources.commit_data import (
    commit_data_resource,
)
from mozreview.resources.commit_rewrite import (
    commit_rewrite_resource,
)
from mozreview.resources.review_request_summary import (
    review_request_summary_resource,
)
from mozreview.signal_handlers import (
    initialize_signal_handlers,
)


SETTINGS_PATH = os.path.join('/', 'mozreview-settings.json')
SETTINGS = None


class ParentJSExtension(JSExtension):
    model_class = 'MRParents.Extension'
    apply_to = review_request_url_names


class MozReviewExtension(Extension):
    metadata = {
        'Name': 'mozreview',
        'Summary': 'MozReview extension to Review Board',
    }

    default_settings = {
        'enabled': False,
        'pulse_host': '',
        'pulse_port': '',
        'pulse_user': '',
        'pulse_password': '',
        'pulse_ssl': False,
        'autoland_try_ui_enabled': False,
        'autoland_url': '',
        'autoland_user': '',
        'autoland_password': '',
        'autoland_testing': False,
        'autoland_import_pullrequest_ui_enabled': False,
        'ldap_url': '',
        'ldap_user': '',
        'ldap_password': '',
    }

    is_configurable = True

    js_extensions = [ParentJSExtension]

    css_bundles = {
        'default': {
            'source_filenames': ['mozreview/css/common.less'],
        },
        'review': {
            'source_filenames': ['mozreview/css/review.less',
                                 'mozreview/css/commits.less'],
        },
        'viewdiff': {
            'source_filenames': ['mozreview/css/viewdiff.less'],
        },
    }
    js_bundles = {
        'default': {
            'source_filenames': ['mozreview/js/logout.js'],
        },
        'filediffreviewer': {
            'source_filenames': ['mozreview/js/models/filediffreviewermodel.js',
                                 'mozreview/js/collections/filediffreviewercollection.js',
                                 'mozreview/js/init_filediffreviewer.js',
                                 'mozreview/js/diffviewer_customizations.js'],
            'apply_to': diffviewer_url_names,
        },
        'import-pullrequest': {
            'source_filenames': ['mozreview/js/import-pullrequest.js',],
            'apply_to': ['import_pullrequest',],
        },
        'reviews': {
            # TODO: Everything will break if init_rr.js is not first in this
            # list.
            'source_filenames': ['mozreview/js/init_rr.js',
                                 'mozreview/js/commits.js',
                                 'mozreview/js/review.js',
                                 'mozreview/js/autoland.js',
                                 'mozreview/js/ui.mozreviewautocomplete.js',]
        },
        'parent-review-requests': {
            'source_filenames': ['mozreview/js/parents.js'],
            'apply_to': review_request_url_names,
        },
    }

    resources = [
        autoland_request_update_resource,
        autoland_trigger_resource,
        batch_review_request_resource,
        batch_review_resource,
        bugzilla_api_key_login_resource,
        commit_data_resource,
        commit_rewrite_resource,
        file_diff_reviewer_resource,
        import_pullrequest_trigger_resource,
        import_pullrequest_update_resource,
        ldap_association_resource,
        review_request_summary_resource,
        try_autoland_trigger_resource,
    ]

    middleware = [
        MozReviewCacheDisableMiddleware,
        MozReviewUserProfileMiddleware,
    ]

    def initialize(self):
        initialize_pulse_handlers(self)

        URLHook(self,
                patterns('', url(r'^mozreview/', include('mozreview.urls'))))

        HeaderDropdownActionHook(self, actions=[{
            'label': 'MozReview',
            'items': [
                {
                    'label': 'User Guide',
                    'url': 'https://mozilla-version-control-tools.readthedocs.org/en/latest/mozreview-user.html',
                },
                {
                    'label': 'Mercurial for Mozillians',
                    'url': 'https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmozilla/index.html',
                },
                {
                    'label': 'Hacking MozReview',
                    'url': 'https://mozilla-version-control-tools.readthedocs.org/en/latest/hacking-mozreview.html',
                },
                {
                    'label': 'File a Bug',
                    'url': 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=MozReview',
                },
            ],
        }])

        ReviewRequestDropdownActionHook(self, actions=[
        {
            'label': 'Automation',
            'id': 'automation-menu',
            'items': [
                {
                    'id': 'autoland-try-trigger',
                    'label': 'Trigger a Try Build',
                    'url': '#',
                },
                {
                    'id': 'autoland-trigger',
                    'label': 'Land Commits',
                    'url': '#',
                },
            ],
        },
        ])

        # Hide fields from all review requests that are not used by Mozilla
        # developers.
        main_fieldset = get_review_request_fieldset('main')
        testing_done_field = get_review_request_field('testing_done')
        if testing_done_field:
            main_fieldset.remove_field(testing_done_field)

        info_fieldset = get_review_request_fieldset('info')
        for field_name in ('branch', 'depends_on', 'blocks'):
            field = get_review_request_field(field_name)
            if field:
                info_fieldset.remove_field(field)

        # We "monkey patch" (yes, I feel dirty) the should_render method on
        # the description field so that it is not rendered for parent review
        # requests.
        description_field = get_review_request_field('description')
        if description_field:
            description_field.should_render = (lambda self, value:
                not is_parent(self.review_request_details))

        # All of our review request styling is injected via
        # review-stylings-css, which in turn loads the review.css static
        # bundle.
        TemplateHook(self, 'base-css', 'mozreview/review-stylings-css.html',
                     apply_to=review_request_url_names)
        TemplateHook(self, 'base-css', 'mozreview/viewdiff-stylings-css.html',
                     apply_to=diffviewer_url_names)
        TemplateHook(self, 'base-scripts-post',
                     'mozreview/review-scripts-js.html',
                     apply_to=review_request_url_names)
        TemplateHook(self, 'base-extrahead',
                     'mozreview/base-extrahead-login-form.html',
                     apply_to=['login'])
        TemplateHook(self, 'before-login-form',
                     'mozreview/before-login-form.html', apply_to=['login'])
        TemplateHook(self, 'after-login-form',
                     'mozreview/after-login-form.html', apply_to=['login'])
        TemplateHook(self, 'base-after-content',
                     'mozreview/scm_level.html')
        TemplateHook(self, 'base-after-content',
                     'mozreview/repository.html')

        ReviewRequestFieldsHook(self, 'main', [CommitsListField])
        # This forces the Commits field to be the top item.
        main_fieldset.field_classes.insert(0,
                                           main_fieldset.field_classes.pop())

        # The above hack forced Commits at the top, but the rest of these
        # fields are fine below the Description.
        ReviewRequestFieldsHook(self, 'main', [CombinedReviewersField])
        ReviewRequestFieldsHook(self, 'main', [TryField])
        ReviewRequestFieldsHook(self, 'main', [BaseCommitField])
        ReviewRequestFieldsHook(self, 'main', [FileDiffReviewerField])

        # We want pull to appear first as it is the more robust way of
        # retrieving changesets.
        ReviewRequestFieldsHook(self, 'info', [PullCommitField])
        ReviewRequestFieldsHook(self, 'info', [ImportCommitField])

        # Use a custom method to calculate a review approval state.
        MozReviewApprovalHook(self)

        # Instantiate the various signal handlers
        initialize_signal_handlers(self)

        HostingServiceHook(self, HMORepository)

        URLHook(self, patterns('',
            url(r'^import-pullrequest/(?P<user>.+)/(?P<repo>.+)/(?P<pullrequest>\d+)/$',
            import_pullrequest, name='import_pullrequest')))

    def shutdown(self):
        # We have to put the TestingDone field back before we shut down
        # in order to get the instance back to its original state.
        main_fieldset = get_review_request_fieldset('main')
        if not get_review_request_field('testing_done'):
            main_fieldset.add_field(TestingDoneField)

        info_fieldset = get_review_request_fieldset('info')
        if not get_review_request_field('branch'):
            info_fieldset.add_field(BranchField)
        if not get_review_request_field('depends_on'):
            info_fieldset.add_field(DependsOnField)
        if not get_review_request_field('blocks'):
            info_fieldset.add_field(BlocksField)

        super(MozReviewExtension, self).shutdown()

    def get_settings(self, key, default=None):
        """This gets settings from the mozreview-settings.json file

        It caches the settings in memory and reloads them if changes are
        detected on disk.

        This code is derived from autoland/autoland/config.py.
        """

        global SETTINGS

        try:
            if SETTINGS is None:
                with open(SETTINGS_PATH, 'r') as f:
                    SETTINGS = json.load(f)
            return SETTINGS.get(key, self.default_settings.get(key, default))
        except IOError:
            logging.error('Could not access settings file (using defaults)'
                          ': %s' % SETTINGS_PATH)
            return self.default_settings.get(key, default)
