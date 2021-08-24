#!/usr/bin/env python

import unittest
import mock

from mozhghooks.check.check_bug_references import BMOAPIClient


class TestBMOAPIClient(unittest.TestCase):
    @mock.patch(
        "mozhghooks.check.check_bug_references.urllibcompat.urlreq.urlopen"
    )
    def test__get(self, mock_urlopen):
        """
        Tests the client's ._get method, which is used by the client to query
        the BMO API. Expects the correct parameters to be passed to
        urlopen.
        """
        client = BMOAPIClient(b"https://example.ca", {})
        mock_path = b"/hello_world"
        mock_params = (
            (b"hello", b"world"),
            (b"hi", b"world2"),
        )
        mock_params_encoded = b"hello=world&hi=world2"
        response = client._get(mock_path, mock_params)

        # Check that we indeed called urlopen and only once.
        self.assertEqual(mock_urlopen.call_count, 1)

        # Check that the URL requested is composed of the base URL (BMO API)
        # plus the path plus the query parameters
        self.assertEqual(
            mock_urlopen.call_args[0][0].get_full_url().encode("utf-8"),
            (client.base_url + mock_path + b"?" + mock_params_encoded),
        )

        # Check that ._get returns the response object of urlopen.
        self.assertEqual(
            response, mock_urlopen(mock_path + mock_params_encoded)
        )

    @mock.patch("mozhghooks.check.check_bug_references.BMOAPIClient._get")
    @mock.patch("mozhghooks.check.check_bug_references.json")
    def test_search_bugs(self, mock_json, mock__get):
        """
        Tests the client's .search_bugs method, which is used by the client to
        filter bug IDs and determine which ones are missing. Expects that the
        URL and parameters be passed correctly to client._get.
        """
        client = BMOAPIClient(b"https://example.ca", {})
        client.search_bugs([b"bug-1", b"bug-2"])

        # Check that we indeed called client._get and that it was called only
        # once.
        self.assertEqual(mock__get.call_count, 1)

        # Check that client._get was called with the correct path.
        self.assertEqual(mock__get.call_args[0][0], b"/bug")

        # Check that the correct parameters are parsed and passed to
        # client._get.
        self.assertEqual(
            mock__get.call_args[0][1],
            ((b"id", b"bug-1,bug-2"), (b"include_fields", b"id"),),
        )

        # TODO: improve coverage for this test.

    @mock.patch("mozhghooks.check.check_bug_references.BMOAPIClient._get")
    def test_get_status_code_for_bug(self, mock__get):
        """
        Tests the client's .get_status_code_for_bug method, which is used by
        the client to fetch a single bug and return the status code of the
        request that is sent by urlopen. Ensures the correct parameters are
        passed to client._get.
        """
        client = BMOAPIClient(b"https://example.ca", {})
        result = client.get_status_code_for_bug(b"bug-3")

        # Check that client._get was indeed called, and only once.
        self.assertEqual(mock__get.call_count, 1)

        # Check that client._get was called with the correct path.
        self.assertEqual(mock__get.call_args[0][0], b"/bug/bug-3")

        # Check that the return value of the method is the status code of the
        # response.
        self.assertEqual(result, mock__get().getcode())


if __name__ == "__main__":
    unittest.main()
