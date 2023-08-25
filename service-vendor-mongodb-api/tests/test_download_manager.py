"""
unit tests for download_manager.py
"""
from unittest import TestCase
from unittest.mock import patch

from tests.external_dependencies import mock_requests_connection_error, mock_requests_connection_timeout, \
    mock_requests_read_timeout


class Test(TestCase):
    """
    main test class
    """
########################################################################################################################
#                                         request_instance                                                             #
########################################################################################################################
    @patch('requests.request', lambda **_kwargs: type("request", (object,), {"status_code": 400, "url": "test"}))
    def test_download_instance_status_400(*_args):
        """
        test post response with status_code 400 that should return false
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", headers="")

    @patch('requests.request', lambda **_kwargs: type("request", (object,), {"status_code": 500, "url": "test"}))
    def test_download_instance_status_500(*_args):
        """
        test post response with status_code 400 that should return false
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", headers="")

    @patch('requests.request', mock_requests_read_timeout)
    def test_request_instance_handle_read_timeout(*_args):
        """
        force readTimeout and test handling exception that should return false to the caller
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", retry=1, headers="")

    @patch('requests.request', mock_requests_connection_timeout)
    def test_request_instance_handle_connection_timeout(*_args):
        """
        force connectionTimeout and test handling exception that should return false to the caller
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", retry=1, headers="")\


    @patch('requests.request', mock_requests_connection_error)
    def test_request_instance_handle_connection_error(*_args):
        """
        force ConnectionError and test handling exception that should return false to the caller
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", retry=1, headers="")
