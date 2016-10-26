# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import unittest

import djblets
import factory
import pytest
import reviewboard.testing
from django.test import RequestFactory as DjangoRequestFactory
from djblets.webapi import errors as rberrors
from mock import call, Mock, patch, sentinel
from reviewboard.diffviewer.models import DiffSet
from reviewboard.reviews import models as rbmodels
from reviewboard.scmtools.models import Repository

from mozreview.resources.batch_review_request import BatchReviewRequestResource
from mozreview.tests.helpers import BaseFactory, UserFactory


class RepositoryFactory(BaseFactory):
    class Meta:
        model = Repository
        strategy = factory.BUILD_STRATEGY


class DiffSetFactory(BaseFactory):
    class Meta:
        model = DiffSet
        strategy = factory.BUILD_STRATEGY


def fake_commit_json(**kwargs):
    """Factory function producing a 'commits' JSON field.

    Caller can provide keyword values to override individual keys.
    """
    # TODO: can we generate this structure using a helper function?
    commits = {
        'squashed': {
            'base_commit_id': '',
            'diff_b64': '',
            'first_public_ancestor': '',
        },
        'individual': [{
            'id': '',
            'author': '',
            'message': 'foo',
            'bug': '',
            'diff_b64': '',
            'precursors': '',
            'first_public_ancestor': '',
        }],
    }
    commits.update(kwargs)
    return commits


def fake_api_post_data(**kwargs):
    """Produce fake data for a batch_review_request API call.

    Caller can provide keyword values to override individual keys.
    """
    # TODO: this is structured data.  We need helper functions here.
    request_data = {
        'username': 'faker',
        'api_key': 'fakeapikey',
        'repo_id': 123,
        'identifier': 'somerridentifier',
        'commits': json.dumps(fake_commit_json()),
    }
    request_data.update(kwargs)
    return request_data


def intersect_dict(dict_a, dict_b):
    """Return the dictionary of intersecting keys between dict a and b"""
    common_keys = set(dict_a).intersection(set(dict_b))
    return dict((k, dict_b[k]) for k in common_keys)


class BatchCreateArgsVerificationTest(unittest.TestCase):

    def test_fail_if_user_missing_verify_diff_perm(self):
        request = DjangoRequestFactory().get('/', data=fake_api_post_data())
        request.user = UserFactory()
        request.user.has_perm = Mock(return_value=False)

        brr = BatchReviewRequestResource()
        response = brr.create(request)

        request.user.has_perm.assert_called_once_with('mozreview.verify_diffset')
        self.assertEqual(response, rberrors.PERMISSION_DENIED)

    @patch('mozreview.resources.batch_review_request.auth_api_key')
    def test_fail_if_bugzilla_auth_missing(self, mock_api_auth_key):
        request = DjangoRequestFactory().get('/', data=fake_api_post_data())
        request.user = UserFactory()
        request.user.has_perm = Mock(return_value=True)

        mock_api_auth_key.return_value = sentinel.fake_failed_WebAPIResponse

        brr = BatchReviewRequestResource()
        response = brr.create(request)

        self.assertEqual(response, sentinel.fake_failed_WebAPIResponse)

    @patch('mozreview.resources.batch_review_request.auth_api_key')
    def test_fail_if_bad_commits_field_json(self, mock_api_auth_key):
        mangled_data = fake_api_post_data(commits='jinx!')
        request = DjangoRequestFactory().get('/', data=mangled_data)
        request.user = UserFactory(username='throw-away')

        # Pass the initial user permission check
        request.user.has_perm = Mock(return_value=True)
        # Pass the user session cleansing step
        request.session = Mock()

        # Create a fake user to carry out the commit operation
        mock_api_auth_key.return_value = UserFactory()

        brr = BatchReviewRequestResource()
        response = brr.create(request)

        self.assertEqual(response[0], rberrors.INVALID_FORM_DATA)

    # TODO Tests for JSON structure validation
    # TODO Tests for JSON values validation


@pytest.mark.django_db
class ProcessSubmissionTest(
    djblets.testing.testcases.TestModelsLoaderMixin,
    reviewboard.testing.TestCase):

    tests_app = 'mozreview'

    def patch_object(self, obj, name, **kwargs):
        """Convenient alternative to the @patch.object() decorator."""
        patcher = patch.object(obj, name, **kwargs)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def spy_on(self, obj, method_name):
        """Wrap a method of an object.  Return a MagicMock that passes all
        calls through to the original method.
        """
        original_method = getattr(obj, method_name)
        return self.patch_object(obj, method_name, wraps=original_method)

    def patch_diffset_creation(self, repository):
        """Create a real diffset for a review request and mock the
        function that returns it.

        The real create_from_data() function hits the database, the filesystem,
        and expects a real diff file.  We can skip all that in this test.
        """
        # We want to pass through all calls to the original manager except
        # for create_from_data(), which we stub out.
        ds_manager = DiffSet.objects
        mock_manager = self.patch_object(DiffSet, 'objects', wraps=ds_manager)

        def fake_create(*args, **kwargs):
            return self.create_diffset(repository=repository)

        mock_manager.create_from_data = fake_create

    def test_squashed_rr_and_child_rr_are_created_if_missing(self):
        bmouser = UserFactory.create(username='bmouser')
        request = Mock(user=bmouser)
        repository = self.create_repository()
        local_site = None
        self.patch_diffset_creation(repository)
        privileged_user = UserFactory.create(
            username='privileged',
            permissions=['verify_diffset']
        )
        commit_id = 'no_such_review_request'
        commits = fake_commit_json()

        create = self.spy_on(rbmodels.ReviewRequest.objects, 'create')

        brr = BatchReviewRequestResource()
        brr._process_submission(
            request,
            local_site,
            bmouser,
            privileged_user,
            repository,
            commit_id,
            commits)

        # The create() method will be called multiple times.  The first call
        # creates our squashed review request if it doesn't exist.  The second
        # call creates a child review request.
        create.assert_has_calls([
            call(
                user=bmouser,
                local_site=local_site,
                commit_id=commit_id,
                repository=repository),
            call(
                user=bmouser,
                local_site=local_site,
                commit_id=None,
                repository=repository),
        ])
