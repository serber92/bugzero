"""
unit tests for download_manager.py
"""
import sys
from unittest import TestCase
from unittest.mock import patch

from tests.external_dependencies import mock_requests_connection_error, mock_requests_connection_timeout, \
    mock_requests_read_timeout


########################################################################################################################
#                                         request_instance                                                             #
########################################################################################################################
class Test1(TestCase):
    """
    testing a post response with status_code 400 that should return false
    """
    @patch(
        'requests.session',
        lambda **_kwargs: type("request", (object,),
                               {"request": lambda *_args, **_kwargs:
                               type("response", (object,), {"status_code": 401, "url": "test", "text": "error test"})}
                               )
    )
    def test_download_instance_status_400(*_args):
        """
        testing a post response with status_code 400 that should return false
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", headers="", retry=1)
        del sys.modules['download_manager']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
class Test2(TestCase):
    """
    testing a post response with json payload and a status_code 400 that should return false
    """
    @patch(
        'requests.session',
        lambda **_kwargs: type("request", (object,),
                               {"request": lambda *_args, **_kwargs:
                               type("response", (object,), {"status_code": 401, "url": "test", "text": "error test"})}
                               )
    )
    def test_download_instance_post_json_status_400(*_args):
        """
        testing a post response with status_code 400 that should return false
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", headers="", json={"test": "test"}, retry=1)
        del sys.modules['download_manager']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
class Test3(TestCase):
    """
    testing a post response with status_code 500 that should return false
    """
    @patch(
        'requests.session',
        lambda **_kwargs: type("request", (object,),
                               {"request": lambda *_args, **_kwargs:
                               type("response", (object,), {"status_code": 500, "url": "test", "text": "error test"})}
                               )
    )
    def test_download_instance_status_500(*_args):
        """
        testing a post response with status_code 400 that should return false
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", headers="", retry=1)
        del sys.modules['download_manager']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
class Test4(TestCase):
    """
    testing a post response with status_code 429 that should return false
    """
    @patch(
        'requests.session',
        lambda **_kwargs: type("request", (object,),
                               {"request": lambda *_args, **_kwargs:
                               type("response", (object,), {"status_code": 429, "url": "test", "text": "error test"})}
                               )
    )
    def test_download_instance_status_429(*_args):
        """
        testing a post response with status_code 429 that should return false
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", headers="", retry=1, rate_limit_sleep=1)
        del sys.modules['download_manager']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
class Test5(TestCase):
    """
    testing a post response with read timeout that should return false
    """
    @patch(
        'requests.session',
        lambda **_kwargs: type("request", (object,),
                               {"request": lambda *_args, **_kwargs:
                               mock_requests_read_timeout()}
                               )
    )
    def test_request_instance_handle_read_timeout(*_args):
        """
        force readTimeout and handling exception that should return false to the caller
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", retry=1, headers="")
        del sys.modules['download_manager']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
class Test6(TestCase):
    """
    testing a post response with connection timeout that should return false
    """
    @patch(
        'requests.session',
        lambda **_kwargs: type("request", (object,),
                               {"request": lambda *_args, **_kwargs:
                               mock_requests_connection_timeout()}
                               )
    )
    def test_request_instance_handle_connection_timeout(*_args):
        """
        force connectionTimeout and handling exception that should return false to the caller
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", retry=1, headers="")
        del sys.modules['download_manager']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
class Test7(TestCase):
    """
    testing a post response with connection error that should return false
    """
    @patch(
        'requests.session',
        lambda **_kwargs: type("request", (object,),
                               {"request": lambda *_args, **_kwargs:
                               mock_requests_connection_error()}
                               )
    )
    def test_request_instance_handle_connection_error(*_args):
        """
        force connectionTimeout and handling exception that should return false to the caller
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", retry=1, headers="")
        del sys.modules['download_manager']
# -------------------------------------------------------------------------------------------------------------------- #


# -------------------------------------------------------------------------------------------------------------------- #
class Test8(TestCase):
    """
    testing a non-session post response with json payload a status_code 400 that should return false
    """
    @patch(
        'requests.request',
        lambda **_kwargs: type("response", (object,), {"status_code": 401, "url": "test", "text": "error test"})
    )
    def test_download_instance_no_session_post_json_status_400(*_args):
        """
        testing a non-session post response with json payload a status_code 400 that should return false
        :param _args:
        :return:
        """
        from download_manager import download_instance
        assert not download_instance(link="test", headers="", json={"test": "test"}, retry=1, session=False)
        del sys.modules['download_manager']
