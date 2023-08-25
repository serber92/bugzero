#!/usr/bin/env python3
"""
updated 2021-06-28
- switch from DynamoDB to Aurora MySQL DB
updated 2021-08-20
- added support for service status updates
- added better exception handling log
"""
import datetime
import importlib
import inspect
import json
import logging.config
import os
import signal
import sys
import traceback

import boto3
from sqlalchemy import or_
from sqlalchemy.exc import OperationalError
from vendor_hpe_api_client import HpeApiClient

from db_client import Database
from vendor_exceptions import LambdaTimeOutException

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
common_service = importlib.import_module("service-common.python.lib.sn_utils")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

VENDOR_PRIORITY_MAP = {
    "cv66000027": "Customer Bulletin (Critical)",
    "cv66000024": "Customer Notice (Routine)",
    "cv66000022": "Customer Advisory (Recommended)",
    "sev10000009": "Customer Bulletin (Critical)",
    "sev10000001": "Customer Notice (Routine)",
    "sev10000010": "Customer Advisory (Recommended)"
}


def insert_bug(bug, db_client, bugs_table):
    """

    :param bug:
    :param db_client:
    :param bugs_table:
    :return:
    """
    updated_bug = 0
    skipped_bug = 0
    inserted_bug = 0
    existing_bug = db_client.conn.query(db_client.base.classes[bugs_table]).filter(
        db_client.base.classes[bugs_table].bugId == bug["bugId"],
        db_client.base.classes[bugs_table].managedProductId == bug["managedProductId"]

    ).first()

    # update existing entries if any of the values have changed ( excluding 'managedProductId' )
    if existing_bug:
        updated = False
        if bug["vendorLastUpdatedDate"] != existing_bug.vendorLastUpdatedDate:
            for key, value in bug.items():
                setattr(existing_bug, key, value)
                updated = True
        if updated:
            existing_bug.updatedAt = datetime.datetime.utcnow()
            updated_bug += 1
        else:
            skipped_bug += 1
    else:
        now_utc = datetime.datetime.utcnow()
        bug = db_client.base.classes[bugs_table](**bug)
        bug.createdAt = now_utc
        bug.updatedAt = now_utc

        db_client.conn.add(bug)
        inserted_bug += 1

    return inserted_bug, updated_bug, skipped_bug


def bugs_discovery(hpe_api_client, product, bugs_date_back, db_client, vendors_products_table, bugs_table):
    """
    get bugs from hpe public api
    :param hpe_api_client:
    :param product:
    :param bugs_date_back:
    :param db_client:
    :param vendors_products_table:
    :param bugs_table:
    :return:
    """
    # ---------------------------------------------------------------------------------------------------------------- #
    #                                                 BUG DISCOVERY                                                    #
    # ---------------------------------------------------------------------------------------------------------------- #
    earliest_bug_date = product.lastExecution if product.lastExecution else bugs_date_back

    vendor_product_id = db_client.conn.query(
        db_client.base.classes[vendors_products_table]
    ).filter(
        db_client.base.classes[vendors_products_table].id == product.vendorProductId,
        ).first().productId

    # get all product oids associated with the product
    product_target_oids = hpe_api_client.get_all_related_product_oids(
        vendor_product_id=vendor_product_id, oid_type='product_search', tab="Products"
    )
    # software_target_oids = hpe_api_client.get_all_related_product_oids(
    #         vendor_product_id=vendor_product_id, oid_type='software_search', tab="DriversandSoftware"
    #     )

    # create a vendorPriorityValue: vendorPriorityLabel dictionary
    priorities = {
        x["vendorPriority"]:  VENDOR_PRIORITY_MAP[str(x["vendorPriority"])] for x in product.vendorPriorities
    }

    # get all bugs for the target_oids and filter by lastExecution and vendorPriorities
    product_bugs = hpe_api_client.get_bugs_by_product_oid(
        managed_product_id=product.id,
        target_oids=product_target_oids,
        product_priorities=priorities,
        earliest_bug_date=earliest_bug_date,
        managed_product_name=product.name
    )

    # get all drivers and software for the target_oids and filter by lastExecution and vendorPriorities
    product_software = hpe_api_client.get_software_by_product_oid(
        managed_product_id=product.id,
        target_oids=vendor_product_id,
        product_priorities=priorities,
        earliest_bug_date=earliest_bug_date,
        managed_product_name=product.name
    )

    for bug in product_bugs + product_software:
        # truncate VARCHAR values that are too long
        for key, value in bug.items():
            if type(
                    getattr(db_client.base.classes[bugs_table], key).prop.columns[0].type
            ).__name__ in ["VARCHAR", "TEXT"]:
                bug[key] = Database.truncate_text_fields(
                    table_class=db_client.base.classes[bugs_table],
                    key=key,
                    value=value
                )
    return product_bugs, product_software


def initiate(*_args, **_kwargs):
    """
       1. get all active hpe clients and set the earliest bug date to retrieve
       2. retrieve new bugs
       3. filter bugs based on earliest bug date
       3. iterate over clients with relevant managed-products families and insert bug to (env)-vendor-bugs-table
    :return:
    """
    # use a signal handler to set an alarm that will invoke
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm((int(_args[1].get_remaining_time_in_millis() / 1000)) - 1)
    vendor_id = "hpe"
    service_id = "hpe-bug-svc"
    service_name = "HPE Bug Service"
    started_timestamp = datetime.datetime.utcnow()
    hpe_api_client = HpeApiClient(
        vendor_id=vendor_id
    )

    # ---------------------------------------------------------------------------------------------------------------- #
    #                                    SERVICE NOW EVENT MANAGEMENT CONFIG                                           #
    # ---------------------------------------------------------------------------------------------------------------- #
    event_class = os.environ["EVENT_CLASS"]
    node = os.environ["NODE"]
    resource = _args[1].function_name
    additional_info = f"log_group_name: {_args[1].log_group_name}\nlog_stream_name: {_args[1].log_stream_name}"

    # ------------------------------------------------------------------------------------------------------------ #
    #                                                 AURORA DB CONFIG                                             #
    # ------------------------------------------------------------------------------------------------------------ #
    managed_products_table = os.environ["MANAGED_PRODUCTS_TABLE"]
    bugs_table = os.environ["BUGS_TABLE"]
    settings_table = os.environ["SETTINGS_TABLE"]
    vendors_table = os.environ["VENDORS_TABLE"]
    vendors_products_table = os.environ["VENDOR_PRODUCTS_TABLE"]
    service_execution_table = os.environ["SERVICE_EXECUTION_TABLE"]
    services_table = os.environ["SERVICES_TABLE"]

    db_client = Database(
        db_host=os.environ["DB_HOST"],
        db_port=os.environ["DB_PORT"],
        db_user=os.environ["DB_USER"],
        db_password=os.environ["DB_PASS"],
        db_name=os.environ["DB_NAME"],
    )

    try:
        # create a new session
        db_client.create_session()

        hpe_config = db_client.conn.query(
            db_client.base.classes[settings_table]
        ).get(vendor_id)
        hpe_vendor_status = db_client.conn.query(
            db_client.base.classes[vendors_table].active
        ).filter_by(id=vendor_id).first()
        if not hpe_config or not hpe_vendor_status or not hpe_vendor_status.active:
            message = f"{vendor_id} vendor services are disabled or not configured"
            logger.error(message)
            raise NotImplementedError(message)

        hpe_config = hpe_config.value

        # ------------------------------------------------------------------------------------------------------------ #
        #                                       MANAGED PRODUCTS VERIFICATION                                          #
        # ------------------------------------------------------------------------------------------------------------ #
        # create a six hours ago timestamp
        last_executed_gap = datetime.datetime.utcnow() - datetime.timedelta(hours=6)

        # get managed products:
        # - IsDisabled not True
        # - LastExecuted >= 6 hours or None
        recently_processed_products = db_client.conn.query(
            db_client.base.classes[managed_products_table].name,
            db_client.base.classes[managed_products_table].lastExecution,
        ).filter(
            db_client.base.classes[managed_products_table].lastExecution > last_executed_gap,
            db_client.base.classes[managed_products_table].isDisabled is not 1,
            db_client.base.classes[managed_products_table].vendorId == vendor_id
        ).all()

        if [u.name for u in recently_processed_products]:
            processed_items = json.dumps(
                [
                    {'name': u.name, 'lastExecution': u.lastExecution}
                    for u in recently_processed_products
                ],
                default=str
            )
            logger.info(
                f"skipping products processed in the last 6 hours - {processed_items}"
            )

        managed_products = db_client.conn.query(
            db_client.base.classes[managed_products_table]
        ).filter(
            or_(
                db_client.base.classes[managed_products_table].lastExecution <= last_executed_gap,
                db_client.base.classes[managed_products_table].lastExecution.is_(None)
            ),
            db_client.base.classes[managed_products_table].isDisabled is not 1,
            db_client.base.classes[managed_products_table].vendorId == vendor_id
        ).all()

        if [u.name for u in managed_products]:
            items_to_process = json.dumps(
                [
                    {'name': u.name, 'lastExecution': u.lastExecution} for u in managed_products
                ], default=str)

            logger.info(
                f"to be processed managed products - {items_to_process}"
            )

            # set the global earliest date to get bugs ( used if a managed products is missing a lastExecution field )
            bugs_date_back = (
                    datetime.datetime.utcnow() - datetime.timedelta(days=int(hpe_config["daysBack"]))
            )

            # retrieve the public api auth key
            aura_config = hpe_api_client.get_aura_config()
            auth_form = hpe_api_client.gen_auth_form(aura_config=aura_config)
            hpe_api_client.get_auth_key(auth_form=auth_form)

            # get the resource names necessary for consuming the api
            hpe_api_client.get_api_data_resource_names()

            # consume the bug API for each managed product
            total_bugs_count = 0
            total_inserted_bugs = 0
            total_updated_bugs = 0
            total_skipped_bug = 0

            for product in managed_products:
                bugs_count = 0
                inserted_bugs = 0
                updated_bugs = 0
                skipped_bugs = 0
                # set the earliest bug date from product data or global config

                product_bugs, product_software = bugs_discovery(
                    hpe_api_client=hpe_api_client, db_client=db_client, bugs_date_back=bugs_date_back,
                    vendors_products_table=vendors_products_table, product=product, bugs_table=bugs_table)

                # insert bugs
                bugs_count += len(product_software)
                bugs_count += len(product_bugs)
                for bug in product_bugs + product_software:
                    inserted_bug, updated_bug, skipped_bug = insert_bug(
                        bug=bug, bugs_table=bugs_table, db_client=db_client)
                    inserted_bugs += inserted_bug
                    updated_bugs += updated_bug
                    skipped_bugs += skipped_bug

                total_bugs_count += bugs_count
                total_inserted_bugs += inserted_bugs
                total_updated_bugs += updated_bugs
                total_skipped_bug += skipped_bugs
                logger.info(
                    f"{product.name} - {bugs_count}/{inserted_bugs}/{updated_bugs}/{skipped_bugs} "
                    f"bugs found/added/updated/skipped"
                )

                # update lastExecution timestamp
                product.lastExecution = datetime.datetime.utcnow()
                db_client.conn.commit()

            logger.info(f"{total_bugs_count}/{total_inserted_bugs}/{total_updated_bugs}/{total_skipped_bug} "
                        f"bugs found/added/updated/skipped")
            message = f"{total_bugs_count} new bugs published"

        #  no new bugs updates
        else:
            logger.info(f"currently there are no products to process")
            message = f"0 new bugs published"

    except (OperationalError, ValueError, ConnectionError, TypeError, json.JSONDecodeError, AttributeError,
            NotImplementedError, LambdaTimeOutException) as e:

        if isinstance(e, OperationalError):
            message = "Database connection error - we are working on getting this fixed as soon as we can"
        else:
            try:
                message = e.args[0]
            except IndexError:
                message = str(e)

        logger.error(f"{str(e)}")

        if isinstance(e, LambdaTimeOutException):
            sns_client = boto3.client('sns')
            event = common_service.sn_event_formatter(
                event_class=event_class, resource=resource, node=node, metric_name=e.__class__.__name__,
                description=traceback.format_exc().replace('"', ""), error_type="Program", severity=1,
                additional_info=additional_info,
                logger=logger
            )
            event_string = json.dumps({"default": json.dumps(event)})
            sns_client.publish(
                TopicArn=os.environ["SNS_TOPIC"], Subject="test", MessageStructure="json", Message=event_string
            )

        elif not isinstance(e, NotImplementedError):
            # generate an sn event record and send to the sns topic
            sns_client = boto3.client('sns')
            event = common_service.sn_event_formatter(
                event_class=event_class, resource=resource, node=node, metric_name=e.__class__.__name__,
                description=traceback.format_exc().replace('"', ""), error_type="Operational", severity=1,
                additional_info=additional_info,
                logger=logger
            )
            event_string = json.dumps({"default": json.dumps(event)})
            sns_client.publish(
                TopicArn=os.environ["SNS_TOPIC"], Subject="test", MessageStructure="json", Message=event_string
            )

        hpe_api_client.bug_zero_vendor_status_update(
            db_client=db_client,
            started_at=started_timestamp,
            services_table=services_table,
            service_execution_table=service_execution_table,
            vendor_id=vendor_id,
            service_id=service_id,
            error=1,
            message=message,
            service_status="ERROR",
            service_name=service_name
        )

        return {
            "message": message
        }

    # update the services & serviceExecutions tables
    hpe_api_client.bug_zero_vendor_status_update(
        service_status="OPERATIONAL",
        db_client=db_client,
        vendor_id=vendor_id,
        service_execution_table=service_execution_table,
        services_table=services_table,
        service_id=service_id,
        started_at=started_timestamp,
        message=message,
        service_name=service_name
    )

    logger.info(message)
    return {
        "message": message
    }


def timeout_handler(_signal, _frame):
    """
    Handle SIGALRM exception when lambda timeout is about to be reached
    :param _signal:
    :param _frame:
    :return:
    """
    raise LambdaTimeOutException


if __name__ == "__main__":  # pragma: no cover
    # when testing, enable stdout logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    initiate(
        "",
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "hpe-bug-svc",
            "log_group_name": "hpe-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 15000
        })
    )
