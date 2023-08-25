"""
created 2021-06-27
"""
import datetime
import json
import logging.config

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base, name_for_collection_relationship
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger()
sql_logger = logging.getLogger('sqlalchemy.engine')


class Database:
    """Aurora Serverless connection class."""

    def __init__(self, db_host, db_user, db_password, db_port, db_name):
        """
        set database connection variables in class instance
        """
        self.host = db_host
        self.username = db_user
        self.password = db_password
        self.port = db_port
        self.dbname = db_name
        self.base = None
        self.conn = None

    def create_session(self):
        """
        Connect to MySQL Database
        :return:
        """
        engine = create_engine(
            f"mysql+pymysql://{self.username}:{self.password}@{self.host}/{self.dbname}"
        )
        self.base = automap_base()

        def _name_for_collection_relationship(base, local_cls, referred_cls, constraint):  # pragma: no cover
            if constraint.name:
                return constraint.name.lower()
            # if this didn't work, revert to the default behavior
            return name_for_collection_relationship(base, local_cls, referred_cls, constraint)

        self.base.prepare(engine, reflect=True, name_for_collection_relationship=_name_for_collection_relationship)
        session_factory = sessionmaker()
        session_factory.configure(bind=engine)
        self.conn = session_factory()

    @staticmethod
    def truncate_text_fields(table_class, key, value, default=1000):
        """
        truncate varchar/text values based on model definition or default value provided
        :param key:
        :param value:
        :param table_class:
        :param default:
        :return:
        """
        max_len = getattr(table_class, key).prop.columns[0].type.length
        # if max len is not defined use default
        if not max_len:
            max_len = default
        if value and len(value) > max_len:
            return value[:max_len - 3] + "..."
        return value

    def get_managed_products(self, managed_products_table, vendor_id):
        """

        :param managed_products_table:
        :param vendor_id:
        :return:
        """
        entries = self.conn.query(
            self.base.classes[managed_products_table]
        ).filter(
            self.base.classes[managed_products_table].vendorId == vendor_id
        ).all()
        return entries

    def get_vendor_config(self, settings_table, vendor_id):
        """

        :param settings_table:
        :param vendor_id:
        :return:
        """
        config = self.conn.query(
            self.base.classes[settings_table]
        ).get(vendor_id)
        if not config:
            return False
        return config

    def get_vendor_status(self, vendors_table, vendor_id):
        """

        :param vendors_table:
        :param vendor_id:
        :return:
        """
        rh_vendor_status = self.conn.query(
            self.base.classes[vendors_table].active
        ).filter_by(id=vendor_id).first()
        if not rh_vendor_status or not rh_vendor_status.active:
            return rh_vendor_status
        return True

    def create_managed_product(
            self, name, versions, vendor_priorities, vendor_statuses, vendor_resolutions, vendor_id,
            managed_products_table
    ):
        """
        create a new manageProduct
        :param name:
        :param vendor_priorities:
        :param vendor_statuses:
        :param vendor_resolutions:
        :param vendor_id:
        :param managed_products_table:
        :param versions:
        :return:
        """
        now_utc = datetime.datetime.utcnow()
        if not self.conn.query(
                self.base.classes[managed_products_table]
        ).filter(
            self.base.classes[managed_products_table].name == name
        ).all():
            new_managed_product = {
                "vendorId": vendor_id,
                "vendorPriorities": vendor_priorities,
                "vendorStatuses": vendor_statuses,
                "vendorData": {
                    "versions": versions,
                    "vendorResolutions": vendor_resolutions,
                },
                "createdAt": now_utc,
                "updatedAt": now_utc,
                "isDisabled": 0,
                "lastExecution": None,
                "name": name
            }
            logger.info(
                f"'{name}' - creating a new managed product | {json.dumps(new_managed_product, default=str)}"
            )
            new_managed_product = self.base.classes[managed_products_table](**new_managed_product)
            self.conn.add(new_managed_product)
            self.conn.commit()
            self.conn.refresh(new_managed_product)
            return new_managed_product
        return False

    def insert_bug_updates(self, bugs, bugs_table):
        """
        1. insert new bugs
        2. update existing bugs
        :param bugs:
        :param bugs_table:
        :return:
        """
        # counters
        counter = {
            "updated_bugs": 0,
            "skipped_bugs": 0,
            "inserted_bugs": 0
        }
        for bug in bugs:
            # truncate VARCHAR values if necessary
            for key, value in bug.items():
                if type(
                        getattr(self.base.classes[bugs_table], key).prop.columns[0].type
                ).__name__ in ["VARCHAR", "TEXT"]:
                    bug[key] = Database.truncate_text_fields(
                        table_class=self.base.classes[bugs_table],
                        key=key,
                        value=value
                    )

            # check for existing bug:
            existing_bug = self.conn.query(
                self.base.classes[bugs_table]
            ).filter(
                self.base.classes[bugs_table].bugId == bug["bugId"],
                self.base.classes[bugs_table].managedProductId == bug["managedProductId"]
            ).first()
            if existing_bug:
                if bug["vendorLastUpdatedDate"] != existing_bug.vendorLastUpdatedDate:
                    for key, value in bug.items():
                        setattr(existing_bug, key, value)
                    existing_bug.updatedAt = datetime.datetime.utcnow()
                    counter['updated_bugs'] += 1
                    logger.info(
                        f"'{bug['vendorData']['vendorProductName']}' - updating bug | {json.dumps(bug, default=str)}"
                    )
                else:
                    counter['skipped_bugs'] += 1
                    continue
            else:
                now_utc = datetime.datetime.utcnow()
                logger.info(
                    f"'{bug['vendorData']['vendorProductName']}' - inserting bug | {json.dumps(bug, default=str)}"
                )
                bug = self.base.classes[bugs_table](**bug)
                bug.createdAt = now_utc
                bug.updatedAt = now_utc

                self.conn.add(bug)
                counter['inserted_bugs'] += 1
        self.conn.commit()
        return counter

    def update_managed_product_versions(self, managed_product, versions):
        """
        update version attribute of a manged product
        :param managed_product:
        :param versions:
        :return:
        """
        logger.info(f"'{managed_product.name}' - updating managed product | versions {versions}")
        managed_product.versions = versions
        managed_product.updatedAt = datetime.datetime.utcnow()
        self.conn.commit()
        self.conn.refresh(managed_product)

    def remove_bugs_by_managed_product_id(self, managed_product, bugs_table):
        """
        remove all bugs associated with a managedProductId
        :param managed_product:
        :param bugs_table:
        :return:
        """
        bugs = self.conn.query(
            self.base.classes[bugs_table]
        ).filter(
            self.base.classes[bugs_table].managedProductId == managed_product.id
        )
        count = bugs.count()
        if count:
            logger.info(f"'{managed_product.name}' - deleting {count} associated bugs")
            bugs.delete()
        self.conn.commit()

    def remove_non_active_managed_products(
            self, active_managed_product_ids, managed_products_table, bugs_table, vendor_id
    ):
        """
        - remove any managedProduct that no longer has an active_ci
        - remove bugs associated with the managedProduct
        :param active_managed_product_ids
        :param managed_products_table
        :param bugs_table
        :param vendor_id
        :return:
        """
        entries = self.conn.query(
            self.base.classes[managed_products_table]
        ).filter(
            self.base.classes[managed_products_table].id.not_in(active_managed_product_ids),
            self.base.classes[managed_products_table].vendorId == vendor_id
        ).all()
        removed_products = 0
        for product in entries:
            logger.info(
                f"'{product.name}' - removing managedProduct and associated bugs | SN CMDB no longer "
                f"includes an active reference to this product")
            # removing associated bugs
            self.remove_bugs_by_managed_product_id(bugs_table=bugs_table, managed_product=product)
            # removing managedProduct
            self.conn.query(self.base.classes[managed_products_table]).filter_by(id=product.id).delete()
            removed_products += 1
        self.conn.commit()
        return removed_products
