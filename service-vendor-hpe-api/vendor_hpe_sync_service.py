#!/usr/bin/env python3
"""
created 2021-04-28
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
from deepdiff import DeepDiff
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


def initiate(*_args, **_kwargs):
    """
       1. generate a request with configured filters to consume hpe public API for all the relevant product
       2a. upsert products to vendorProductsTable
       2a. insert new product family if missing
    :return:
    """
    # use a signal handler to set an alarm that will invoke
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm((int(_args[1].get_remaining_time_in_millis() / 1000)) - 1)

    vendor_id = "hpe"
    service_id = "hpe-sync-svc"
    service_name = "HPE Sync"

    # source description required to retrieve the most updated resource name for the products data point
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
    vendor_products_table = os.environ["VENDOR_PRODUCTS_TABLE"]
    vendor_product_families_table = os.environ["VENDOR_PRODUCT_FAMILIES_TABLE"]
    settings_table = os.environ["SETTINGS_TABLE"]
    vendors_table = os.environ["VENDORS_TABLE"]
    service_execution_table = os.environ["SERVICE_EXECUTION_TABLE"]
    services_table = os.environ["SERVICES_TABLE"]

    # create a new db_client
    logger.info("creating Aurora Serverless client")
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

        # retrieve vendor config
        hpe_config = db_client.conn.query(
            db_client.base.classes[settings_table]
        ).get(vendor_id)

        # verify that the vendor was not disabled by the user
        hpe_vendor_status = db_client.conn.query(
            db_client.base.classes[vendors_table].active
        ).filter_by(id=vendor_id).first()

        if not hpe_config or not hpe_vendor_status or not hpe_vendor_status.active:
            message = f"{vendor_id} vendor services are disabled or not configured"
            raise NotImplementedError(message)

    # ---------------------------------------------------------------------------------------------------------------- #
    #                                                  HPE PRODUCTS SEARCH                                             #
    # ---------------------------------------------------------------------------------------------------------------- #
        # retrieve the public api auth key
        aura_config = hpe_api_client.get_aura_config()
        auth_form = hpe_api_client.gen_auth_form(aura_config=aura_config)
        hpe_api_client.get_auth_key(auth_form=auth_form)

        # get the resource names necessary for consuming the api
        hpe_api_client.get_api_data_resource_names()

        # search for all hpe products
        search = products_search(
            hpe_api_client=hpe_api_client,
            vendor_product_families_table=vendor_product_families_table,
            vendor_products_table=vendor_products_table,
            vendor_id=vendor_id,
            db_client=db_client,
        )
        if not search:
            raise ConnectionError("Vendor sync error - HPE data APIs are not available")

    except (OperationalError, ValueError, ConnectionError, TypeError, NotImplementedError, LambdaTimeOutException) as e:

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
        message="Sync process completed successfully",
        service_name=service_name
    )
    logger.info(search)
    return {"message": search}


def compare_product_update(vendor_product_entry, existing_vendor_product):
    """
    check for discoverd product update
    :param vendor_product_entry:
    :param existing_vendor_product:
    :return:
    """
    updated = False
    for key, value in vendor_product_entry.items():
        # compare dictionaries and list
        if isinstance(value, (dict, list)):
            diff = DeepDiff(value, existing_vendor_product.__dict__[key], ignore_order=True)
            if diff:
                setattr(existing_vendor_product, key, value)
                updated = True

        elif value != str(existing_vendor_product.__dict__[key]):
            setattr(existing_vendor_product, key, value)
            updated = True
    return updated


def products_search(hpe_api_client, vendor_id, db_client, vendor_products_table,
                    vendor_product_families_table):
    """
    search for all available hpe products based on vendor_hpe_search_filters.json
    :param hpe_api_client:
    :param vendor_id:
    :param db_client:
    :param vendor_products_table:
    :param vendor_product_families_table:
    :return:
    """
    logger.info("searching HPE API for products")
    new_products = 0
    updated_products = 0
    skipped_products = 0
    with open("vendor_hpe_search_filters.json", "r") as search_filters:
        filters = json.loads(search_filters.read())
        for product, filters in filters["vendorSearchFilters"].items():
            # get all existing products from the API for the given product type
            products = hpe_api_client.get_products(
                product_type=product
            )
            include_filters = [fl for fl in filters if fl['filterType'] == "include"]
            exclude_filters = [fl for fl in filters if fl['filterType'] == "exclude"]
            temp_prod = []

            # iterate over search filters
            for fl in include_filters:
                for x in products:
                    if [
                        kw for kw in fl["filterKw"] if kw.lower() in x["raw"][fl["filterFieldName"]].lower()
                    ]:
                        temp_prod.append(x)
            for fl in exclude_filters:
                temp_prod = [
                    x for x in temp_prod if not [
                        kw for kw in fl["filterKw"] if kw.lower() in x["raw"][fl["filterFieldName"]].lower()
                    ]
                ]

            # gather existing products and insert new entries if exist
            products = temp_prod
            dedup = set()

            for p in products:
                if p['raw']['kmpmoid'] in dedup:
                    continue
                dedup.add(p['raw']['kmpmoid'])
                utc_now = datetime.datetime.utcnow()
                vendor_product_entry = {
                    'name': p['raw']['kmpmname'],
                    'productId': p['raw']['kmpmoid'],
                    'productUrl':
                        f"https://support.hpe.com/hpesc/public/km/product/{p['raw']['kmpmoid']}/{p['raw']['urihash']}",
                    'vendorId': vendor_id
                }
                existing_vendor_product = db_client.conn.query(
                    db_client.base.classes[vendor_products_table]
                ).filter(
                    db_client.base.classes[vendor_products_table].productId == [
                        vendor_product_entry["productId"]
                    ]
                ).first()

                # update existing entries if any of the values have changed ( excluding 'managedProductId' )
                if existing_vendor_product:
                    if compare_product_update(
                            existing_vendor_product=existing_vendor_product, vendor_product_entry=vendor_product_entry
                    ):
                        logger.info(f"{existing_vendor_product.name} - updating vendorProduct entry")
                        existing_vendor_product.updatedAt = utc_now
                        updated_products += 1
                    else:
                        skipped_products += 1
                else:
                    new_products += 1
                    vendor_product_entry["active"] = 0
                    vendor_product_entry["updatedAt"] = utc_now
                    vendor_product_entry["createdAt"] = utc_now
                    vendor_product_entry["vendorData"] = {
                        "category": p['raw']['kmpmlevel1name'],
                        "categoryId": p['raw']['kmpmlevel1name'],
                        "categoryLevel2": p['raw']['kmpmlevel2name'],
                        'categoryLevel3': p['raw']['kmpmlevel3name'],
                        'categoryLevel4': p['raw']['kmpmlevel4name'],
                        'categoryLevel5': p['raw']['kmpmlevel5name'],
                        "categoryLevel2Id": p['raw']['kmpmlevel2oid'],
                        'categoryLevel3Id': p['raw']['kmpmlevel3oid'],
                        'categoryLevel4Id': p['raw']['kmpmlevel4oid'],
                        'categoryLevel5Id': p['raw']['kmpmlevel5oid']
                    }

                    # insert the productFamily if missing
                    vendor_product_family_entry = {
                        "name": vendor_product_entry["vendorData"]["category"],
                        "productFamilyId": p['raw']['kmpmlevel1oid'],
                        "vendorId": vendor_id,
                        "active": 1,
                        "createdAt": utc_now,
                        "updatedAt": utc_now,
                    }

                    existing_product_family = db_client.conn.query(
                        db_client.base.classes[vendor_product_families_table].id
                    ).filter(
                        db_client.base.classes[vendor_product_families_table].productFamilyId == [
                            vendor_product_family_entry["productFamilyId"]
                        ]
                    ).first()

                    if not existing_product_family:
                        logger.info(f"{vendor_product_family_entry['name']} - inserting new vendorProductFamily entry")
                        db_client.conn.add(
                            db_client.base.classes[vendor_product_families_table](**vendor_product_family_entry)
                        )
                        db_client.conn.commit()
                        existing_product_family = db_client.conn.query(
                            db_client.base.classes[vendor_product_families_table].id
                        ).filter(
                            db_client.base.classes[vendor_product_families_table].productFamilyId == [
                                vendor_product_family_entry["productFamilyId"]
                            ]
                        ).first()

                    vendor_product_entry["vendorProductFamilyId"] = existing_product_family.id

                    logger.info(f"{vendor_product_entry['name']} - inserting new vendorProduct entry")
                    db_client.conn.add(
                        db_client.base.classes[vendor_products_table](**vendor_product_entry)
                    )

            db_client.conn.commit()
    return f"{new_products}/{updated_products}/{skipped_products} vendor products added/updated/skipped"


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
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 150000
        })
    )
