"""
unit tests for db_client.py
"""
import os
import sys
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch

from tests.external_dependencies import mock_env, mock_varchar_table, mock_varchar_table_missing_length, \
    mock_formatted_bugs, mock_to_execute_access_server_managed_product


class Test(TestCase):
    """
    main testing class
    """
    ####################################################################################################################
    #                                                    init                                                          #
    ####################################################################################################################
    @patch.dict(os.environ, mock_env())
    def test_initiate_success(*_args):
        """
        simple instantiation of Database class
        :param _args:
        :return:
        """
        from db_client import Database
        db_client = Database(
            db_host="", db_user="", db_password="", db_port=3306, db_name=""
        )
        assert isinstance(db_client, Database)
        del sys.modules['db_client']

    ####################################################################################################################
    #                                                    create session                                                #
    ####################################################################################################################
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
            db_host="", db_user="", db_password="", db_port=3306, db_name=""
        )
        db_client.create_session()
        assert db_client.conn
        del sys.modules['db_client']

    ####################################################################################################################
    #                                                    validate_varchar                                              #
    ####################################################################################################################
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
        del sys.modules['db_client']

    @patch.dict(os.environ, mock_env())
    def test_validate_varchar_missing_max_length(*_args):
        """
        ensure if the table class is missing a max length ( TEXT type ) the validate varchar is returning a truncated
        version of the value < 1000.
        :param _args:
        :return:
        """
        from db_client import Database
        table_class = mock_varchar_table_missing_length
        key = "vendorData"
        value_x2 = "value" * 2
        assert Database.validate_varchar(table_class=table_class, key=key, value=value_x2) == value_x2
        del sys.modules['db_client']

    ####################################################################################################################
    #                                                    get_vendor_config                                             #
    ####################################################################################################################
    @patch.dict(os.environ, mock_env())
    def test_get_vendor_config_missing(*_args):
        """
        when a vendor config is missing return false
        :param _args:
        :return:
        """
        from db_client import Database
        instance = type(
            "mockDbClient",
            (object,), {
                "conn": type("mockObject", (object,), {"query": lambda *args, **kwargs:
                type("mockObject", (object,), {"get": lambda *args, **kwargs: False})}),
                "base": MagicMock()
            }
        )
        instance.return_value = False
        config = Database.get_settings(self=instance, settings_table="", vendor_id="veeam")
        assert not config
        del sys.modules['db_client']

    ####################################################################################################################
    #                                                    get_vendor_status                                             #
    ####################################################################################################################
    @patch.dict(os.environ, mock_env())
    def test_get_vendor_status_false(*_args):
        """
        when a vendor status is missing or set to false
        :param _args:
        :return:
        """
        from db_client import Database
        instance = type(
            "mockDbClient",
            (object,), {
                "conn":
                    type("mockObject", (object,),
                         {"query": lambda *args, **kwargs:
                         type("mockObject", (object,),
                              {"filter_by": lambda *args, **kwargs:
                              type("mockObject", (object,), {"first": lambda *args, **kwargs: False})})}),
                "base": MagicMock()
            }
        )
        instance.return_value = False
        config = Database.get_vendor(self=instance, vendors_table="", vendor_id="msft")
        assert not config
        del sys.modules['db_client']

    ####################################################################################################################
    #                                                    create_managed_product                                        #
    ####################################################################################################################
    @patch.dict(os.environ, mock_env())
    def test_get_vendor_create_managed_product(*_args):
        """
        testing a successful creation of managedProduct
        :param _args:
        :return:
        """
        from db_client import Database
        instance = type(
            "mockDbClient",
            (object,), {
                "conn":
                    type("mockObject", (object,),
                         {
                             "query": lambda *args, **kwargs: type("mockObject", (object,),
                                                                   {"filter": lambda *args, **kwargs:
                                                                   type("mockObject", (object,),
                                                                        {"all": lambda *args, **kwargs: False})}),
                             "add": lambda *args: True,
                             "commit": lambda *args: True,
                             "refresh": lambda *args: True,
                         },

                         ),
                "base": MagicMock()
            }
        )
        instance.return_value = False
        new_managed_product = Database.create_managed_product(
            self=instance, managed_products_table="", name="", vendor_id="msft",
            service_settings={"vendorPriorities": [], "vendorStatuses": []}
        )
        assert new_managed_product
        del sys.modules['db_client']

    ####################################################################################################################
    #                                               insert_bug_updates                                                 #
    ####################################################################################################################
    @patch.dict(os.environ, mock_env())
    @patch('sqlalchemy.orm.attributes')
    def test_insert_bug_updates(*_args):
        """
        requirement: testing a successful insertion of 2 new bugs
        description: the execution should return a counter dictionary where 'inserted_bugs' == 2
        mock: bugs list with 2 entries, db_client
        :param _args:
        :return:
        """
        from db_client import Database
        instance = type(
            "mockDbClient",
            (object,), {
                "conn":
                    type("mockObject", (object,),
                         {
                             "query": lambda *args, **kwargs: type("mockObject", (object,),
                                                                   {"filter": lambda *_args, **_kwargs:
                                                                   type("mockObject", (object,),
                                                                        {
                                                                            "all": lambda *args, **kwargs: False,
                                                                            "first": lambda *args, **kwargs: False
                                                                        })
                                                                    }),
                             "add": lambda *args: True,
                             "commit": lambda *args: True,
                             "refresh": lambda *args: True,
                         },

                         ),
                "base": MagicMock()
            }
        )
        instance.return_value = False
        execution = Database.insert_bug_updates(
            self=instance, bugs=mock_formatted_bugs, bugs_table="", product_name="test"
        )
        assert execution["inserted_bugs"] == 5
        del sys.modules['db_client']

    ####################################################################################################################
    #                                             remove_bugs_by_managed_product_id                                    #
    ####################################################################################################################
    @patch.dict(os.environ, mock_env())
    @patch('sqlalchemy.orm.attributes')
    def test_remove_bugs_by_managed_product_id(*_args):
        """
        requirement: testing a successful deletion of all bugs for a given managedProduct.id
        description: the execution should not raise an error
        mock: db client
        :param _args:
        :return:
        """
        from db_client import Database
        instance = type(
            "mockDbClient",
            (object,), {
                "conn":
                    type("mockObject", (object,),
                         {
                             "query": lambda *args, **kwargs: type("mockObject", (object,),
                                                                   {"filter": lambda *_args, **_kwargs:
                                                                   type("mockObject", (object,),
                                                                        {
                                                                            "all": lambda *args, **kwargs: False,
                                                                            "first": lambda *args, **kwargs: False,
                                                                            "count": lambda *args, **kwargs: 2,
                                                                            "delete": lambda *args, **kwargs: 0
                                                                        })
                                                                    }),
                             "add": lambda *args: True,
                             "commit": lambda *args: True,
                             "refresh": lambda *args: True,
                         },

                         ),
                "base": MagicMock()
            }
        )
        instance.return_value = False
        Database.remove_bugs_by_managed_product_id(
            self=instance, bugs_table="", managed_product=mock_to_execute_access_server_managed_product[0]
        )
        assert True
        del sys.modules['db_client']

    ####################################################################################################################
    #                                            remove_non_active_managed_products                                    #
    ####################################################################################################################
    @patch.dict(os.environ, mock_env())
    @patch('sqlalchemy.orm.attributes')
    def test_remove_non_active_managed_products(*_args):
        """
        requirement: testing a successful removal of a managedProduct
        description: the execution should not raise an error
        mock: db client
        :param _args:
        :return:
        """
        from db_client import Database
        instance = type(
            "mockDbClient",
            (object,), {
                "conn":
                    type("mockObject", (object,),
                         {
                             "query": lambda *args, **kwargs: type("mockObject", (object,),
                                                                   {"filter": lambda *_args, **_kwargs:
                                                                   type("mockObject", (object,),
                                                                        {
                                                                            "all":
                                                                                lambda *args, **kwargs: [
                                                                                    type(
                                                                                        "mockManagedProduct", (object,),
                                                                                        {"id": 1, "name": 1}
                                                                                    ),
                                                                                    type(
                                                                                        "mockManagedProduct", (object,),
                                                                                        {"id": 2, "name": 2}
                                                                                    ),
                                                                                    type(
                                                                                        "mockManagedProduct", (object,),
                                                                                        {"id": 3, "name": 3}
                                                                                    ),

                                                                                ],
                                                                            "first": lambda *args, **kwargs: False,
                                                                            "count": lambda *args, **kwargs: 2,
                                                                            "delete": lambda *args, **kwargs: 0
                                                                        }),
                                                                    "filter_by": lambda *args, **kwargs:
                                                                    type("mockObject", (object,),
                                                                         {"delete": lambda *args, **kwargs: 0
                                                                          })}),
                             "add": lambda *args: True,
                             "commit": lambda *args: True,
                             "refresh": lambda *args: True,
                         },

                         ),
                "base": MagicMock(),
                "remove_bugs_by_managed_product_id": lambda *_args, **_kwargs: ""
            }
        )
        instance.return_value = False
        count = Database.remove_non_active_managed_products(
            self=instance, bugs_table="", managed_products_table="", active_managed_product_ids=[1, 2, 3],
            vendor_id="aws"
        )
        assert count == 3
        del sys.modules['db_client']
