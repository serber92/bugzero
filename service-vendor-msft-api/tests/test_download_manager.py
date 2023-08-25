"""
unit tests for download_manager.py
"""
from unittest import TestCase
from unittest.mock import patch

from tests.external_dependencies import mock_requests_connection_error, mock_requests_connection_timeout, \
    mock_requests_read_timeout


class Test(TestCase):
    """
    main testing class
    """
########################################################################################################################
#                                         request_instance                                                             #
########################################################################################################################
    @patch('requests.get', lambda **_kwargs: type("request", (object,), {"status_code": 404, "url": "test"}))
    def test_download_instance_status_404(*_args):
        """
        testing post response with status_code 400 that should return false
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", headers="", session=False)

    @patch('requests.post', lambda **_kwargs: type("request", (object,), {"status_code": 503, "url": "test"}))
    def test_download_instance_status_503(*_args):
        """
        testing post response with status_code 400 that should return false
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", headers="", method='POST', session=False)

    @patch('requests.get', mock_requests_read_timeout)
    def test_request_instance_handle_read_timeout(*_args):
        """
        force readTimeout and testing handling exception that should return false to the caller
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", retry=1, headers="", session=False)

    @patch('requests.get', mock_requests_connection_timeout)
    def test_request_instance_handle_connection_timeout(*_args):
        """
        force connectionTimeout and testing handling exception that should return false to the caller
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", retry=1, headers="", session=False)

    @patch('requests.get', mock_requests_connection_error)
    def test_request_instance_handle_connection_error(*_args):
        """
        force ConnectionError and testing handling exception that should return false to the caller
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", retry=1, headers="", session=False)

    @patch('requests.get', lambda **_kwargs: type("request", (object,), {"status_code": 200, "url": "test"}))
    def test_successful_session_request(*_args):
        """
        return a status 200 request for a successful session
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert download_instance(link="test", retry=1, headers="", session=False)
