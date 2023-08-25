"""
unit tests for download_manager.py
"""
from unittest import TestCase
from unittest.mock import patch

from tests.external_dependencies import mock_session, mock_session_w_post_404, SessionMock


class Test(TestCase):
    """
    main test class
    """
########################################################################################################################
#                                         request_instance                                                             #
########################################################################################################################
    @patch('requests.post', lambda **_kwargs: type("request", (object,), {"status_code": 400, "url": "test"}))
    def test_request_instance_post_status_400(*_args):
        """
        test post response with status_code 400 that should return false
        :param _args:
        :return:
        """
        from download_manager import request_instance
        assert not request_instance(url="test", headers="", post=True, session=False)

    @patch('requests.get', lambda **_kwargs: type("request", (object,), {"status_code": 400, "url": "test"}))
    def test_request_instance_status_400(*_args):
        """
        test post response with status_code 400 that should return false
        :param _args:
        :return:
        """
        from download_manager import request_instance
        assert not request_instance(url="test", headers="", post=False, session=False)

    @patch('requests.get', lambda **_kwargs: type("request", (object,), {"status_code": 200, "url": "test"}))
    def test_request_instance_w_headers(*_args):
        """
        :param _args:
        :return:
        """
        from download_manager import request_instance
        assert request_instance(url="test", headers={"test": ""}, post=False, session=False).status_code == 200    \


    @patch('requests.get', lambda **_kwargs: type("request", (object,), {"status_code": 404, "url": "test"}))
    def test_request_instance_ignore_404(*_args):
        """
        special ignore_404 argument passed returning responses with 404 status setting them to status 200
        :param _args:
        :return:
        """
        from download_manager import request_instance
        assert request_instance(
            url="test", headers={"test": ""}, post=False, session=False, ignore_404=True
        ).status_code == 200

    @patch('requests.post', lambda **_kwargs: type("request", (object,), {"status_code": 400, "url": "test"}))
    def test_request_instance_post_status_400_with_json(*_args):
        """
        test post response with json form resulting in status_code 400 that should return false
        :param _args:
        :return:
        """
        from download_manager import request_instance
        assert not request_instance(url="test", json='{"post_form": ""}', post=True, session=False)

    def test_request_instance_post_session_success(*_args):
        """
        test a successful post request done with a requests.session object
        :param _args:
        :return:
        """
        from download_manager import request_instance
        assert request_instance(url="test", session=mock_session, post=True).status_code == 200

    def test_request_instance_session_w_headers_success(*_args):
        """
        test a successful post request done with a requests.session object using headers
        :param _args:
        :return:
        """
        from download_manager import request_instance
        assert request_instance(
            url="test", headers={"headers": ""}, session=mock_session, post=False,
        ).status_code == 200

    def test_request_instance_session_success(*_args):
        """
        test a successful post request done with a requests.session object using headers
        :param _args:
        :return:
        """
    from download_manager import request_instance
    assert request_instance(
        url="test", headers="", session=mock_session, post=False,
    ).status_code == 200

    def test_request_instance_post_session_404(*_args):
        """
        test a failed status 404 post request done with a requests.session object
        :param _args:
        :return:
        """
        from download_manager import request_instance
        assert not request_instance(url="test", session=mock_session_w_post_404, post=True)

    def test_request_instance_handle_read_timeout(*_args):
        """
        force readTimeout and test handling exception
        :param _args:
        :return:
        """
        from download_manager import request_instance
        assert not request_instance(url="test", session=SessionMock, post=True, retry=1)
