"""
created 2021-06-27
"""
import datetime
import json
import logging.config

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base, name_for_collection_relationship
from sqlalchemy.orm import attributes
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

        def _name_for_collection_relationship(base, local_cls, referred_cls, constraint):
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

    def get_service_config(self, settings_table, vendor_id):
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

    def get_vendor_settings(self, vendors_table, vendor_id):
        """

        :param vendors_table:
        :param vendor_id:
        :return:
        """
        vendor_settings = self.conn.query(
            self.base.classes[vendors_table]
        ).filter_by(id=vendor_id).first()
        if not vendor_settings or not vendor_settings.active:
            return False
        return vendor_settings

    def get_managed_product(self, managed_products_table, vendor_id, product_name):
        """
        get managed product by name
        :param managed_products_table:
        :param product_name:
        :param vendor_id:
        :return:
        """
        entries = self.conn.query(
            self.base.classes[managed_products_table]
        ).filter(
            self.base.classes[managed_products_table].vendorId == vendor_id,
            self.base.classes[managed_products_table].name == product_name
        ).all()
        return entries

    def update_managed_product_versions(self, managed_product, versions):
        """
        update version attribute of a manged product
        :param managed_product:
        :param versions:
        :return:
        """
        logger.info(
            f"'{managed_product.name}' - updating managed product | os version(s) {sorted(list(versions))}"
        )
        if not managed_product.vendorData:
            managed_product.vendorData = {}
        attributes.flag_modified(managed_product, "vendorData")
        managed_product.vendorData["productSoftwareVersions"] = sorted(list(versions))
        managed_product.updatedAt = datetime.datetime.utcnow()
        self.conn.commit()
        self.conn.refresh(managed_product)

    def create_managed_product(
            self, name, versions, vendor_id, managed_products_table, service_settings
    ):
        """
        create a new manageProduct
        :param name:
        :param vendor_id:
        :param managed_products_table:
        :param versions:
        :param service_settings:
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
                "vendorData": {
                    "productSoftwareVersions": sorted(versions),
                },
                "vendorPriorities": service_settings['vendorPriorities'],
                "vendorStatuses": service_settings['vendorStatuses'],
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

    def insert_bug_updates(self, bugs, bugs_table, product_name):
        """
        1. insert new bugs
        2. update existing bugs
        :param bugs:
        :param bugs_table:
        :param product_name:
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
                        f"'{product_name}' - updating bug | {json.dumps(bug, default=str)}"
                    )
                else:
                    counter['skipped_bugs'] += 1
                    continue
            else:
                now_utc = datetime.datetime.utcnow()
                logger.info(
                    f"'{product_name}' - inserting bug | {json.dumps(bug, default=str)}"
                )
                bug = self.base.classes[bugs_table](**bug)
                bug.createdAt = now_utc
                bug.updatedAt = now_utc

                self.conn.add(bug)
                counter['inserted_bugs'] += 1
        self.conn.commit()
        return counter

    def update_account_orgs(self, account_orgs, service_config):
        """
        - upsert vmware account organizations to vendorData in the service setting entry
        - new organizations are added with disabled == 1 and must be enabled from the vendor configuration in the UI
        :param account_orgs:
        :param service_config:
        :return:
        """
        new_orgs = 0
        existing_orgs = service_config.value.get("accountOrgs", [])
        existing_org_ids = [x["orgId"] for x in existing_orgs]
        for org in account_orgs:
            org_id = org["refLink"].split("/")[-1]
            if org_id in existing_org_ids:
                continue
            existing_org_ids.append(org_id)
            new_orgs += 1
            existing_orgs.append({
                "name": org["displayName"],
                "orgId": org_id,
                'orgRefLink': org["refLink"],
                "disabled": 0
            })
        if new_orgs:
            # sort by customer name for easy UI orientation
            sorted_orgs = sorted(existing_orgs, key=lambda x: x['name'])
            attributes.flag_modified(service_config, "value")
            service_config.value["accountOrgs"] = sorted_orgs
            service_config.updatedAt = datetime.datetime.utcnow()
            self.conn.commit()
            self.conn.refresh(service_config)

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
        - remove any managedProduct that didn't match products in the skyline inventory
        - remove bugs associated with the managedProduct
        :param active_managed_product_ids
        :param managed_products_table
        :param vendor_id
        :param bugs_table
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
                f"'{product.name}' - removing managedProduct and associated bugs | skyline inventory no longer "
                f"includes a reference to this product")
            # removing associated bugs
            self.remove_bugs_by_managed_product_id(bugs_table=bugs_table, managed_product=product)
            # removing managedProduct
            self.conn.query(self.base.classes[managed_products_table]).filter_by(id=product.id).delete()
            removed_products += 1
        self.conn.commit()
        return removed_products
