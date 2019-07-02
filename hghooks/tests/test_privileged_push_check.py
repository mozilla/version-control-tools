from unittest import TestCase
from mock import Mock, MagicMock, call
import mock
import re

from mozhghooks.check.privileged_push_check import PriviligedPushCheck


class TestPriviligedPushCheck(TestCase):
    a_set_of_unprivileged_group_affiliations = {
        "group_1",
        "group_2",
        "group_3",
        "group_4",
    }
    a_set_of_scm_level_3_group_affiliations = {
        "group_1",
        PriviligedPushCheck.ACTIVE_SCM_LEVEL_3,
        "group_3",
        "group_4",
    }
    a_set_of_scm_allow_direct_push_group_affiliations = {
        "group_1",
        "group_2",
        "group_3",
        PriviligedPushCheck.ACTIVE_SCM_ALLOW_DIRECT_PUSH,
    }

    def create_multiple_ctx_list(self, number_of_ctx=3):
        # create a mocked set of changesets in a linear parent/child ownership structure.
        ctx_mock_list = []
        for x in range(number_of_ctx):
            ctx_mock = MagicMock()
            ctx_mock.hex.return_value.__getitem__.return_value = str(x) * 12
            ctx_mock.description.return_value = "commit %s" % x
            ctx_mock_list.append(ctx_mock)
        for parent, child in zip(ctx_mock_list, ctx_mock_list[1:]):
            parent.children.return_value = [child]
        ctx_mock_list[-1].children.return_value = []
        return ctx_mock_list

    def test_magicwords_and_justification_regular_expression(self):
        sample_source_and_expected_result = (
            # this is a collection of tuples of the form:
            #   (string_to_test, expected_result)
            ("standard boring changeset (Bug 12345) r=lars", False),
            ("%s because I want to" % PriviligedPushCheck.MAGIC_WORDS, True),
            (
                "standard boring changeset (Bug 12345) r=lars\n"
                "and this is multiline and has no magic words",
                False,
            ),
            (
                "standard boring changeset (Bug 12345) r=lars\n"
                "this is multiline\n"
                "and has the right magic words and justification\n"
                "%s because I want to" % PriviligedPushCheck.MAGIC_WORDS,
                True,
            ),
            (
                "standard boring changeset (Bug 12345) r=lars\n"
                "and this is multiline - with justification on a separate line\n"
                "%s\n"
                "because I want to" % PriviligedPushCheck.MAGIC_WORDS,
                True,
            ),
            (
                "standard boring changeset (Bug 12345) r=lars\n"
                "and this is multiline - with missing justification\n"
                "%s" % PriviligedPushCheck.MAGIC_WORDS,
                False,
            ),
        )

        for source, expected_result in sample_source_and_expected_result:
            self.assertEqual(
                bool(
                    PriviligedPushCheck.MAGICWORDS_WITH_JUSTIFICATION_RE.search(source)
                ),
                expected_result,
                'magicwords & justification not found:\n"""%s"""' % source,
            )

    def test_relevant__success(self):
        # setup
        repo_mock = Mock()
        repo_mock.root = "/repo/hg/mozilla/mozilla-central"
        ui_mock = Mock()
        ui_mock.config.return_value = "something_bogus, mozilla-central, other_bogus"
        check_object = PriviligedPushCheck(ui=ui_mock, repo=repo_mock, info=Mock())
        # the tested call
        result = check_object.relevant()
        # verifying test results
        ui_mock.config.assert_called_with("mozilla", "priviliged_push_repo_list")
        self.assertTrue(result)

    def test_relevant__success_flaky_config(self):
        # setup
        repo_mock = Mock()
        repo_mock.root = "/repo/hg/mozilla/mozilla-central"
        ui_mock = Mock()
        ui_mock.config.return_value = "    mozilla-central   , other_bogus,,"
        check_object = PriviligedPushCheck(ui=ui_mock, repo=repo_mock, info=Mock())
        # the tested call
        result = check_object.relevant()
        # verifying test results
        ui_mock.config.assert_called_with("mozilla", "priviliged_push_repo_list")
        self.assertTrue(result)

    def test_relevant__success_single_entry_config(self):
        # setup
        repo_mock = Mock()
        repo_mock.root = "/repo/hg/mozilla/mozilla-central"
        ui_mock = Mock()
        ui_mock.config.return_value = "mozilla-central"
        check_object = PriviligedPushCheck(ui=ui_mock, repo=repo_mock, info=Mock())
        # the tested call
        result = check_object.relevant()
        # verifying test results
        ui_mock.config.assert_called_with("mozilla", "priviliged_push_repo_list")
        self.assertTrue(result)

    def test_relevant__negative(self):
        repo_mock = Mock()
        repo_mock.root = "/repo/hg/mozilla/mozilla-central"
        ui_mock = Mock()
        ui_mock.config.return_value = "something_bogus, other_bogus"
        check_object = PriviligedPushCheck(ui=ui_mock, repo=repo_mock, info=Mock())
        # the tested call
        result = check_object.relevant()
        # verifying test results
        ui_mock.config.assert_called_with("mozilla", "priviliged_push_repo_list")
        self.assertFalse(result)

    def test_relevant__negative_no_data(self):
        repo_mock = Mock()
        repo_mock.root = ""
        ui_mock = Mock()
        ui_mock.config.return_value = "something_bogus, other_bogus"
        check_object = PriviligedPushCheck(ui=ui_mock, repo=repo_mock, info=Mock())
        # the tested call
        result = check_object.relevant()
        # verifying test results
        ui_mock.config.assert_called_with("mozilla", "priviliged_push_repo_list")
        self.assertFalse(result)

    @mock.patch("mozhghooks.check.privileged_push_check.sentry_sdk.init")
    @mock.patch("mozhghooks.check.privileged_push_check.sentry_sdk.capture_message")
    def test_log_push_attempt__success_using_sentry(
        self, sentry_sdk_capture_message_mock, sentry_sdk_init_mock
    ):
        # setup
        message = "this is a Sentry Event message"
        ui_mock = Mock()
        ui_mock.config.return_value = "a_sentry_dsn"
        check_object = PriviligedPushCheck(ui=ui_mock, repo=Mock(), info=Mock())
        # the tested call
        check_object._log_push_attempt(message)
        # verifying test results
        ui_mock.config.assert_called_with("mozilla", "sentry_dsn")
        sentry_sdk_init_mock.assert_called_once_with("a_sentry_dsn")
        sentry_sdk_capture_message_mock.assert_called_once_with(message)

    @mock.patch("mozhghooks.check.privileged_push_check.sentry_sdk.init")
    @mock.patch("mozhghooks.check.privileged_push_check.sentry_sdk.capture_message")
    def test_log_push_attempt__success_without_using_sentry(
        self, sentry_sdk_capture_message_mock, sentry_sdk_init_mock
    ):
        # setup
        message = "this is a Sentry Event message"
        ui_mock = Mock()
        ui_mock.config.return_value = ""
        check_object = PriviligedPushCheck(ui=ui_mock, repo=Mock(), info=Mock())
        # the tested call
        check_object._log_push_attempt(message)
        # verifying test results
        ui_mock.config.assert_called_with("mozilla", "sentry_dsn")
        ui_mock.write.assert_called_with("%s\n" % message)
        sentry_sdk_init_mock.assert_not_called()
        sentry_sdk_capture_message_mock.assert_not_called()

    @mock.patch("mozhghooks.check.privileged_push_check.sentry_sdk.init")
    @mock.patch("mozhghooks.check.privileged_push_check.sentry_sdk.capture_message")
    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_log_push_attempt_sentry_failure(
        self, print_banner_mock, sentry_sdk_capture_message_mock, sentry_sdk_init_mock
    ):
        # setup
        message = "this is a Sentry Event message"

        class SentryConnectionFailure(Exception):
            pass

        raised_exception = SentryConnectionFailure("oops")
        sentry_sdk_init_mock.side_effect = raised_exception
        ui_mock = Mock()
        ui_mock.config.return_value = "some DSN"
        check_object = PriviligedPushCheck(ui=ui_mock, repo=Mock(), info=Mock())
        # the tested call
        check_object._log_push_attempt(message),
        # verifying test results
        ui_mock.config.assert_called_with("mozilla", "sentry_dsn")
        sentry_sdk_init_mock.assert_called_once()
        print_banner_mock.assert_called_with(
            ui_mock,
            "warning",
            check_object.SENTRY_FAILURE_WARNING_MESSAGE % repr(raised_exception),
        )

    @mock.patch("os.environ.get")
    @mock.patch("mozhghooks.check.privileged_push_check.get_active_scm_groups")
    def test_get_user_and_group_affiliations__for_valid_username(
        self, get_scm_groups_mock, os_environ_get_mock
    ):
        """return a valid user name and a set of group affiliations"""
        # setup
        a_username = "wilma@mozilla.com"
        os_environ_get_mock.return_value = a_username
        get_scm_groups_mock.return_value = self.a_set_of_unprivileged_group_affiliations
        check_object = PriviligedPushCheck(ui=Mock(), repo=Mock(), info=Mock())
        # the tested method
        result = check_object._get_user_and_group_affiliations()
        # verifying test results
        os_environ_get_mock.assert_called_once_with("USER", None)
        get_scm_groups_mock.assert_called_once_with(a_username)
        self.assertEqual(
            result, (a_username, self.a_set_of_unprivileged_group_affiliations)
        )

    @mock.patch("os.environ.get")
    @mock.patch("mozhghooks.check.privileged_push_check.get_active_scm_groups")
    def test_get_user_and_group_affiliations__for_bad_username(
        self, get_scm_groups_mock, os_environ_get_mock
    ):
        """return a bad username and an empty set of group affiliations"""
        # setup
        a_username = None
        os_environ_get_mock.return_value = a_username
        check_object = PriviligedPushCheck(ui=Mock(), repo=Mock(), info=Mock())
        # the invocation of the tested method
        result = check_object._get_user_and_group_affiliations()
        # verifying test results
        os_environ_get_mock.assert_called_once_with("USER", None)
        get_scm_groups_mock.assert_not_called()
        self.assertEqual(result, (None, []))

    def test_has_justification__for_no_magic(self):
        """test user_has_justification_and_can_push for the case where SCM Level 3 is present
        but there are no magic words"""
        # setup
        check_object = PriviligedPushCheck(ui=Mock(), repo=Mock(), info=Mock())
        description = (
            "changeset with neither magic nor justification (Bug 12345) r=lars"
        )
        # the tested call:
        result = check_object._has_justification(description)
        # verifying test results
        self.assertEqual(result, False)

    def test_has_justification__for_magic_justification(self):
        """test user_has_justification_and_can_push for the case where SCM Level 3 is present
        and there are both magic words and a justification"""
        # setup
        check_object = PriviligedPushCheck(ui=Mock(), repo=Mock(), info=Mock())
        description = (
            "standard boring changeset (Bug 12345) r=lars\n"
            "%s because I really really want to"
        ) % check_object.MAGIC_WORDS
        # the tested call:
        result = check_object._has_justification(description)
        # verifying test results
        self.assertEqual(result, True)

    def test_has_justification__for_magic_no_justification(self):
        """test user_has_justification_and_can_push for the case where SCM Level 3 is present
        and there are magic words but no justification"""
        # setup
        check_object = PriviligedPushCheck(ui=Mock(), repo=Mock(), info=Mock())
        description = (
            "standard boring changeset (Bug 12345) r=lars\n%s"
            % check_object.MAGIC_WORDS
        )
        # the tested call:
        result = check_object._has_justification(description)
        # verifying test results
        self.assertEqual(result, False)

    @mock.patch(
        "mozhghooks.check.privileged_push_check.PriviligedPushCheck._get_user_and_group_affiliations"
    )
    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_pre__for_ldap_exception(
        self, print_banner_mock, get_user_and_group_affiliations_mock
    ):
        # setup
        get_user_and_group_affiliations_mock.side_effect = Exception("LDAP Fails")
        ui_mock = Mock()
        check_object = PriviligedPushCheck(ui=ui_mock, repo=Mock(), info=Mock())
        # the tested call:
        check_object.pre("node")
        # verifying test results
        print_banner_mock.assert_called_with(
            ui_mock,
            "error",
            check_object.LDAP_USER_EXCEPTION_FAILURE_MESSAGE
            % "Exception('LDAP Fails',)",
        )

    @mock.patch(
        "mozhghooks.check.privileged_push_check.PriviligedPushCheck._get_user_and_group_affiliations"
    )
    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_pre__for_ldap_no_user(
        self, print_banner_mock, get_user_and_group_affiliations_mock
    ):
        # setup
        get_user_and_group_affiliations_mock.return_value = (None, [])
        ui_mock = Mock()
        check_object = PriviligedPushCheck(ui=ui_mock, repo=Mock(), info=Mock())
        # the tested call:
        check_object.pre("node")
        # verifying test results
        print_banner_mock.assert_called_with(
            ui_mock, "error", check_object.LDAP_USER_FAILURE_MESSAGE
        )

    @mock.patch(
        "mozhghooks.check.privileged_push_check.PriviligedPushCheck._get_user_and_group_affiliations"
    )
    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_pre__for_no_privileged_group(
        self, print_banner_mock, get_user_and_group_affiliations_mock
    ):
        # setup
        get_user_and_group_affiliations_mock.return_value = (
            "someone@mozilla.com",
            self.a_set_of_unprivileged_group_affiliations,
        )
        ui_mock = Mock()
        check_object = PriviligedPushCheck(ui=ui_mock, repo=Mock(), info=Mock())
        # the tested call:
        check_object.pre("node")
        # verifying test results
        self.assertTrue(check_object.privilege_level is None)
        print_banner_mock.assert_called_with(
            ui_mock, "error", check_object.INSUFFICIENT_PRIVILEGE_FAILURE_MESSAGE
        )

    @mock.patch(
        "mozhghooks.check.privileged_push_check.PriviligedPushCheck._get_user_and_group_affiliations"
    )
    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_pre__for_scm_level_1_group(
        self, print_banner_mock, get_user_and_group_affiliations_mock
    ):
        # setup
        get_user_and_group_affiliations_mock.return_value = (
            "someone@mozilla.com",
            self.a_set_of_scm_level_3_group_affiliations,
        )
        check_object = PriviligedPushCheck(ui=Mock(), repo=Mock(), info=Mock())
        # the tested call:
        check_object.pre("node")
        # verifying test results
        self.assertEqual(check_object.privilege_level, check_object.ACTIVE_SCM_LEVEL_3)
        print_banner_mock.assert_not_called()

    @mock.patch(
        "mozhghooks.check.privileged_push_check.PriviligedPushCheck._get_user_and_group_affiliations"
    )
    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_pre__for_scm_allow_direct_push_group(
        self, print_banner_mock, get_user_and_group_affiliations_mock
    ):
        # setup
        get_user_and_group_affiliations_mock.return_value = (
            "someone@mozilla.com",
            self.a_set_of_scm_allow_direct_push_group_affiliations,
        )
        check_object = PriviligedPushCheck(ui=Mock(), repo=Mock(), info=Mock())
        # the tested call:
        check_object.pre("node")
        # verifying test results
        self.assertEqual(
            check_object.privilege_level, check_object.ACTIVE_SCM_ALLOW_DIRECT_PUSH
        )
        print_banner_mock.assert_not_called()

    @mock.patch(
        "mozhghooks.check.privileged_push_check.PriviligedPushCheck._has_justification"
    )
    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_check__for_no_privilege(self, print_banner_mock, has_justification_mock):
        # setup
        check_object = PriviligedPushCheck(ui=Mock(), repo=Mock(), info=Mock())
        check_object.privilege_level = None
        # the tested call:
        result = check_object.check(Mock())
        # verifying test results
        self.assertFalse(result)
        has_justification_mock.assert_not_called()
        print_banner_mock.assert_not_called()

    @mock.patch(
        "mozhghooks.check.privileged_push_check.PriviligedPushCheck._has_justification"
    )
    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_check__for_unknown_privilege(
        self, print_banner_mock, has_justification_mock
    ):
        # setup
        ui_mock = Mock()
        ctx_mock = MagicMock()
        ctx_mock.hex.return_value.__getitem__.return_value = "012345689AB"
        check_object = PriviligedPushCheck(ui=ui_mock, repo=Mock(), info=Mock())
        check_object.privilege_level = "Fred and Wilma"
        check_object.first_ctx_rev = None
        # the tested call:
        result = check_object.check(ctx_mock)
        # verifying test results
        self.assertFalse(result)
        has_justification_mock.assert_not_called()
        print_banner_mock.assert_called_with(
            ui_mock, "error", check_object.INTERNAL_ERROR_MESSAGE
        )

    @mock.patch(
        "mozhghooks.check.privileged_push_check.PriviligedPushCheck._has_justification"
    )
    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_check__for_scm_allow_direct_push__single_commit(
        self, print_banner_mock, has_justification_mock
    ):
        # setup
        check_object = PriviligedPushCheck(ui=Mock(), repo=Mock(), info=Mock())
        check_object.privilege_level = check_object.ACTIVE_SCM_ALLOW_DIRECT_PUSH
        check_object.first_ctx_rev = None
        ctx_mock = MagicMock()
        ctx_mock.hex.return_value.__getitem__.return_value = "012345689AB"
        # the tested call:
        result = check_object.check(ctx_mock)
        # verifying test results
        self.assertTrue(result)
        self.assertEqual(check_object.first_ctx_rev, "012345689AB")
        has_justification_mock.assert_not_called()
        print_banner_mock.assert_not_called()

    @mock.patch(
        "mozhghooks.check.privileged_push_check.PriviligedPushCheck._has_justification"
    )
    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_check__for_scm_allow_direct_push__multiple_commit(
        self, print_banner_mock, has_justification_mock
    ):
        # setup
        check_object = PriviligedPushCheck(ui=Mock(), repo=Mock(), info=Mock())
        check_object.privilege_level = check_object.ACTIVE_SCM_ALLOW_DIRECT_PUSH
        check_object.first_ctx_rev = None
        ctx_mock_list = self.create_multiple_ctx_list(3)
        # the tested call:
        for a_ctx in ctx_mock_list:
            result = check_object.check(a_ctx)
            # verify interim results
            self.assertTrue(result)
            self.assertTrue(check_object.first_ctx_rev, "0" * 12)
        # verifying test results
        has_justification_mock.assert_not_called()
        print_banner_mock.assert_not_called()

    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_check__for_scm_level_3__single_commit_with_justification(
        self, print_banner_mock
    ):
        # setup
        check_object = PriviligedPushCheck(ui=Mock(), repo=Mock(), info=Mock())
        check_object.privilege_level = check_object.ACTIVE_SCM_ALLOW_DIRECT_PUSH
        check_object.first_ctx_rev = None
        ctx_mock = MagicMock()
        ctx_mock.hex.return_value.__getitem__.return_value = "012345689AB"
        ctx_mock.children.return_value = []
        ctx_mock.description.return_value = "hello\nPRIVILEGED PUSH: I deserve to push"
        # the tested call:
        result = check_object.check(ctx_mock)
        # verifying test results
        self.assertTrue(result)
        self.assertEqual(check_object.first_ctx_rev, "012345689AB")
        print_banner_mock.assert_not_called()

    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_check__for_scm_level_3__single_commit_without_justification(
        self, print_banner_mock
    ):
        # setup
        ui_mock = Mock()
        check_object = PriviligedPushCheck(ui=ui_mock, repo=Mock(), info=Mock())
        check_object.privilege_level = check_object.ACTIVE_SCM_LEVEL_3
        check_object.first_ctx_rev = None
        ctx_mock = MagicMock()
        ctx_mock.hex.return_value.__getitem__.return_value = "012345689AB"
        ctx_mock.children.return_value = []
        ctx_mock.description.return_value = "hello"
        # the tested call:
        result = check_object.check(ctx_mock)
        # verifying test results
        self.assertFalse(result)
        self.assertEqual(check_object.first_ctx_rev, "012345689AB")
        print_banner_mock.assert_called_with(
            ui_mock, "error", check_object.SCM_LEVEL_3_PUSH_ERROR_MESSAGE
        )

    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_check__for_scm_level_3__multiple_commit_with_justification(
        self, print_banner_mock
    ):
        # setup
        check_object = PriviligedPushCheck(ui=Mock(), repo=Mock(), info=Mock())
        check_object.privilege_level = check_object.ACTIVE_SCM_LEVEL_3
        check_object.first_ctx_rev = None
        ctx_mock_list = self.create_multiple_ctx_list(3)
        ctx_mock_list[
            -1
        ].description.return_value = "PRIVILEGED PUSH: yes, I get to do this"
        # the tested call:
        for a_ctx in ctx_mock_list:
            result = check_object.check(a_ctx)
            # verify interim results
            self.assertTrue(result)
            self.assertTrue(check_object.first_ctx_rev, "0" * 12)
        # verifying test results
        print_banner_mock.assert_not_called()

    @mock.patch(
        "mozhghooks.check.privileged_push_check.PriviligedPushCheck._log_push_attempt"
    )
    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_post_check__for_scm_allow_direct_push(
        self, print_banner_mock, log_push_attempt_mock
    ):
        # setup
        check_object = PriviligedPushCheck(ui=Mock(), repo=Mock(), info=Mock())
        check_object.privilege_level = check_object.ACTIVE_SCM_ALLOW_DIRECT_PUSH
        check_object.first_ctx_rev = "701"
        check_object.user_name = "wilma@mozilla.com"
        # the tested call:
        result = check_object.post_check()
        # verifying test results
        self.assertTrue(result)
        log_push_attempt_mock.assert_called_with(
            check_object.SUCCESS_FOR_SCM_ALLOW_DIRECT_PUSH_LOG_MESSAGE
            % (check_object.first_ctx_rev, check_object.user_name)
        )
        print_banner_mock.assert_not_called()

    @mock.patch(
        "mozhghooks.check.privileged_push_check.PriviligedPushCheck._log_push_attempt"
    )
    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_post_check__for_scm_level_3(
        self, print_banner_mock, log_push_attempt_mock
    ):
        # setup
        check_object = PriviligedPushCheck(ui=Mock(), repo=Mock(), info=Mock())
        check_object.privilege_level = check_object.ACTIVE_SCM_LEVEL_3
        check_object.first_ctx_rev = "701"
        check_object.user_name = "wilma@mozilla.com"
        # the tested call:
        result = check_object.post_check()
        # verifying test results
        self.assertTrue(result)
        log_push_attempt_mock.assert_called_with(
            check_object.SUCCESS_FOR_SCM_LEVEL_3_LOG_MESSAGE
            % (check_object.first_ctx_rev, check_object.user_name)
        )
        print_banner_mock.assert_not_called()

    @mock.patch(
        "mozhghooks.check.privileged_push_check.PriviligedPushCheck._log_push_attempt"
    )
    @mock.patch("mozhghooks.check.privileged_push_check.print_banner")
    def test_post_check__for_scm_level_3(
        self, print_banner_mock, log_push_attempt_mock
    ):
        # setup
        ui_mock = Mock()
        check_object = PriviligedPushCheck(ui=ui_mock, repo=Mock(), info=Mock())
        check_object.privilege_level = "unknown_level"
        check_object.first_ctx_rev = "701"
        check_object.user_name = "wilma@mozilla.com"
        # the tested call:
        result = check_object.post_check()
        # verifying test results
        self.assertFalse(result)
        print_banner_mock.assert_called_with(
            ui_mock, "error", check_object.INTERNAL_ERROR_MESSAGE
        )
