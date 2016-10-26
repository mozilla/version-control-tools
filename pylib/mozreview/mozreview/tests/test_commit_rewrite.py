# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import unittest

import factory
from django.db.models import signals
from django.test import RequestFactory as DjangoRequestFactory
from djblets.webapi import errors as rberrors
from mock import patch
from reviewboard.diffviewer.models import DiffSetHistory
from reviewboard.reviews import models as rbmodels

from mozreview import errors as mrerrors, models as mrmodels
from mozreview.extra_data import COMMITS_KEY
from mozreview.resources.commit_rewrite import CommitRewriteResource
from mozreview.tests.helpers import BaseFactory, UserFactory


class DiffSetHistoryFactory(BaseFactory):
    class Meta:
        model = DiffSetHistory
        strategy = factory.BUILD_STRATEGY


# Reviewboard's post-review-creation signal hooks try to touch the database,
# so we have to switch them off
@factory.django.mute_signals(signals.post_init)
class ReviewRequestFactory(BaseFactory):
    # Review Requests are made up of a summary/parent/squashed review request
    # and a bunch of child review requests.
    # The "parent" request is squashed and aggregated.
    # The "child" requests are for individual commits.  They have associated
    # reviews and reviewers.
    class Meta:
        model = rbmodels.ReviewRequest
        strategy = factory.BUILD_STRATEGY

    id = factory.Sequence(int)
    submitter = factory.SubFactory(UserFactory)
    description = 'foo'
    # This object is created automatically by the custom Manager for
    # ReviewRequest.objects.create()
    diffset_history = factory.SubFactory(DiffSetHistoryFactory)

    @factory.post_generation
    def approved(review_request, create, extracted, **kwargs):
        # The `.approved` property is a complex lazy calculation on
        # ReviewRequest objects.  We'll short-circuit it here.

        if extracted is None:
            # No bool provided by caller, set a default value
            extracted = True

        review_request._approved = extracted


class ReviewFactory(BaseFactory):
    class Meta:
        model = rbmodels.Review
        strategy = factory.BUILD_STRATEGY

    public = True
    user = factory.SubFactory(UserFactory)
    review_request = factory.SubFactory(ReviewRequestFactory)


class CommitDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = mrmodels.CommitData
        strategy = factory.BUILD_STRATEGY

    extra_data = factory.LazyFunction(dict)

    @factory.post_generation
    def reviews(commit_data, create, extracted, **kwargs):
        # extra_data is a complex JSON field, serialized and de-serialized at
        # database read/write time.  We'll streamline setting the field's value
        # here.
        # To build the list the user has to pass a special form:
        #   [parent-review [child-review-1, child-review-2, ...]]
        if not extracted:
            return
        parent_review, child_reviews = extracted

        # The COMMITS_KEY field is JSON-encoded as a list of lists, like so:
        # [['commitid1', db-obj-id-for-commit-1],
        #  ['commitid2', db-obj-id-for-commit-2], ...]
        reviews = []
        for i, child_request in enumerate(child_reviews):
            commit_id = 'commitidforrequestnumber' + str(child_request.id)
            reviews.append([commit_id, child_request.id])
        commit_data.set_for(parent_review, COMMITS_KEY, json.dumps(reviews))


def fake_get(gettable_objects_list):
    """A fake Model.objects.get() function.  Takes a list of fake objects.
    Returns a function that, when given the 'id=' keyword argument, returns that
    key from the dict.
    """
    fake_ids_dict = dict((obj.id, obj) for obj in gettable_objects_list)

    def _fake_get(**kwargs):
        return fake_ids_dict[kwargs.get('id')]

    return _fake_get


class APICallValidationTest(unittest.TestCase):
    @patch.object(rbmodels.ReviewRequest.objects, 'get')
    def test_wrong_id_returns_does_not_exist(self, mock_get):
        mock_get.side_effect = rbmodels.ReviewRequest.DoesNotExist
        request = DjangoRequestFactory().get('/')
        crr = CommitRewriteResource()
        response = crr.get(request, review_request=123)
        self.assertEqual(response, rberrors.DOES_NOT_EXIST)

    @patch.object(rbmodels.ReviewRequest, 'objects')
    @patch('mozreview.resources.commit_rewrite.get_parent_rr')
    def test_review_has_no_parents_returns_does_not_exist(self,
                                                          mock_get_parent_rr,
                                                          mock_get):
        # FIXME this test name appears to be wrong?  The first set
        # of code in CommitRewriteResource.get() asserts that the review is
        # a child commit.  The *second* assertion in CommitRewriteResource.get()
        # checks that the review is also a parent of another review?
        review = ReviewRequestFactory()

        # Return our fake review from the database
        mock_get.get = fake_get([review])

        # Return false from checking that our review has a parent.
        mock_get_parent_rr.return_value = None

        request = DjangoRequestFactory().get('/')
        crr = CommitRewriteResource()
        response = crr.get(request, review_request=review.id)
        self.assertEqual(response, rberrors.DOES_NOT_EXIST)

    @patch.object(rbmodels.ReviewRequest.objects, 'get')
    @patch('mozreview.resources.commit_rewrite.get_parent_rr')
    @patch('mozreview.resources.commit_rewrite.fetch_commit_data')
    @patch('mozreview.resources.commit_rewrite.is_parent')
    def test_review_not_parent_returns_not_parent(self, mock_is_parent,
                                                  mock_fetch_commit_data,
                                                  mock_get_parent_rr, mock_get):
        review = ReviewRequestFactory()

        # Return our review from database calls.
        mock_get.return_value = review

        # Return our review as the parent to get past first parent check.
        mock_get_parent_rr.return_value = review

        # Return fake commit data from the database.
        mock_fetch_commit_data.return_value = CommitDataFactory()

        # Return false from database check that our review is a parent review.
        mock_is_parent.return_value = False

        request = DjangoRequestFactory().get('/')
        crr = CommitRewriteResource()
        response = crr.get(request, review_request=review.id)
        self.assertEqual(response, mrerrors.NOT_PARENT)


class SummaryRewriteTest(unittest.TestCase):

    def create_patch(self, name):
        patcher = patch(name)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def setup_fake_db(self, parent_request, child_requests,
                      reviews):
        # Create mocks and stubs for all indirect inputs to the method under
        # test.

        # Return our reviews from database calls.
        mock_objects = patch.object(rbmodels.ReviewRequest, 'objects').start()
        self.addCleanup(mock_objects.stop)
        mock_objects.get = fake_get([parent_request] + child_requests)

        # Build fake commit data to match our requests
        commit_data = CommitDataFactory(
            reviews=[parent_request, child_requests])

        # Return fake commit data from the database.
        mock_cd = self.create_patch(
            'mozreview.resources.commit_rewrite.fetch_commit_data')
        mock_cd.return_value = commit_data

        # Return true for all parent checks.
        mock_get_parent_rr = self.create_patch(
            'mozreview.resources.commit_rewrite.get_parent_rr')
        mock_get_parent_rr.return_value = parent_request

        mock_is_parent = self.create_patch(
            'mozreview.resources.commit_rewrite.is_parent')
        mock_is_parent.return_value = True

        # Return our fake reviews from the database.
        mock_gen_latest_reviews = self.create_patch(
            'mozreview.resources.commit_rewrite.gen_latest_reviews')
        mock_gen_latest_reviews.return_value = reviews

        # Return fake Ship It! flag from the database.  The value does not
        # matter.
        mock_has_shipit_carryforward = self.create_patch(
            'mozreview.resources.commit_rewrite.has_shipit_carryforward')
        mock_has_shipit_carryforward.return_value = True

    def test_reviewing_myself_rewrites_summary(self):
        viking = UserFactory(username='viking')
        parent_request = ReviewRequestFactory(submitter=viking)
        child_request = ReviewRequestFactory(
            submitter=viking, description="Bug 1 r?viking")

        # Create an approved review.  The reviewer is the same as the submitter.
        reviews = [ReviewFactory(user=viking, ship_it=True)]

        self.setup_fake_db(parent_request, [child_request], reviews)

        # Build the request and view.
        request = DjangoRequestFactory().get('/')
        request.user = parent_request.submitter
        crr = CommitRewriteResource()
        response = crr.get(request, review_request=parent_request.id)

        self.assertNotIsInstance(response, rberrors.WebAPIError)
        self.assertEqual(response[0], 200)
        # FIXME: is there a better way to unwrap this nested response value?
        summary = response[1]['commits'][0]['summary']
        self.assertNotIn('r?viking', summary)
        self.assertIn('r=viking', summary)

    def test_unapproved_child_request_fails_operation(self):
        parent_request = ReviewRequestFactory()
        child_requests = ReviewRequestFactory.build_batch(3, approved=True)
        child_requests.append(ReviewRequestFactory(approved=False))
        # The ship_it status of the review itself does not matter.
        reviews = [ReviewFactory()]

        self.setup_fake_db(parent_request, child_requests, reviews)

        # Build request and view.
        request = DjangoRequestFactory().get('/')
        request.user = parent_request.submitter
        crr = CommitRewriteResource()
        response = crr.get(request, review_request=parent_request.id)

        self.assertEqual(response, mrerrors.AUTOLAND_REVIEW_NOT_APPROVED)

    def test_approved_with_no_valid_reviews_changes_reviewer_to_submitter(self):
        viking = UserFactory(username='viking')
        parent_request = ReviewRequestFactory(submitter=viking)
        child_request = ReviewRequestFactory(
            submitter=viking, description="Bug 1 r?foo")
        reviews = []

        self.setup_fake_db(parent_request, [child_request], reviews)

        # Build the request and view.
        request = DjangoRequestFactory().get('/')
        request.user = parent_request.submitter
        crr = CommitRewriteResource()
        response = crr.get(request, review_request=parent_request.id)

        self.assertNotIsInstance(response, rberrors.WebAPIError)
        self.assertEqual(response[0], 200)
        # FIXME: is there a better way to unwrap this nested response value?
        summary = response[1]['commits'][0]['summary']
        self.assertNotIn('r=foo', summary)
        self.assertNotIn('r?foo', summary)
        self.assertIn('r=viking', summary)

    def test_all_commits_are_rewritten_when_all_reviews_approved(self):
        submitter = UserFactory(username='monk')
        reviewer = UserFactory(username='viking')
        parent_request = ReviewRequestFactory(
            description='Bug 1 r?viking',
            submitter=submitter,
            approved=True)
        reviews = ReviewFactory.build_batch(
            2,
            ship_it=True,
            user=reviewer,
            review_request__submitter=submitter,
            review_request__description='Bug 1 r?viking')
        child_requests = [review.review_request for review in reviews]

        self.setup_fake_db(parent_request, child_requests, reviews)

        # Build the request and view.
        request = DjangoRequestFactory().get('/')
        # FIXME: who is the right party to make this API request?
        request.user = submitter
        crr = CommitRewriteResource()
        response = crr.get(request, review_request=parent_request.id)

        self.assertNotIsInstance(response, rberrors.WebAPIError)
        self.assertEqual(response[0], 200)

        # Assert that the parent request commit summary is rewritten
        # FIXME: is there a better way to unwrap this nested response value?
        summary0 = response[1]['commits'][0]['summary']
        self.assertNotIn('monk', summary0)
        self.assertNotIn('r?viking', summary0)
        self.assertIn('r=viking', summary0)

        # Assert that the child request's commit summary is rewritten
        summary1 = response[1]['commits'][1]['summary']
        self.assertNotIn('monk', summary1)
        self.assertNotIn('r?viking', summary1)
        self.assertIn('r=viking', summary1)
