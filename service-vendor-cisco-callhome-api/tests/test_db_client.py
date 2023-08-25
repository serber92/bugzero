"""
unit tests for db_client.py
"""
import os
from unittest import TestCase
from unittest.mock import patch

from tests.external_dependencies import mock_env, mock_varchar_table


class Test(TestCase):
    """
    main test class
    """
########################################################################################################################
#                                                    init                                                             #
########################################################################################################################
    @patch.dict(os.environ, mock_env())
    def test_initiate_success(*_args):
        """
        simple instantiation of Database class
        :param _args:
        :return:
        """
        from db_client import Database
        db_client = Database(
            db_host="", db_user="", db_password="", db_port="3360", db_name=""
        )
        assert isinstance(db_client, Database)

########################################################################################################################
#                                                    create session                                                    #
########################################################################################################################
    @patch('sqlalchemy.create_engine', lambda *_args, **_kwargs: True)
    @patch(
        'sqlalchemy.ext.automap.automap_base', lambda *_args, **_kwargs:
        type('', (object,), {"prepare": lambda *_args, **_kwargs: True})
    )
    @patch(
        'sqlalchemy.ext.automap.AutomapBase.prepare', lambda *_args, **_kwargs:
        type('', (object,), {"prepare": lambda *_args, **_kwargs: True})
    )
    @patch(
        'sqlalchemy.orm.sessionmaker', lambda **_kwargs:
        type('', (object,), {"configure": lambda *_args, **_kwargs: True})
    )
    @patch.dict(os.environ, mock_env())
    def test_create_session(*_args):
        """
        a successful session creation will result in assigment of self.conn
        :param _args:
        :return:
        """
        from db_client import Database
        db_client = Database(
            db_host="", db_user="", db_password="", db_port="3360", db_name=""
        )
        db_client.create_session()
        assert db_client.conn

########################################################################################################################
#                                                    validate_varchar                                                  #
########################################################################################################################
    @patch.dict(os.environ, mock_env())
    def test_validate_varchar(*_args):
        """
        ensure that the validate varchar is returning a truncated version of the value ( max len = 8 )
        :param _args:
        :return:
        """
        from db_client import Database
        table_class = mock_varchar_table
        key = "vendorData"
        value_x2 = "value" * 2
        truncated_assertion_value = "value..."
        assert Database.validate_varchar(table_class=table_class, key=key, value=value_x2) == truncated_assertion_value
