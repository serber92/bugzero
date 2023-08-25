#!/usr/bin/env python3
"""
created 2021-08-06
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
from sqlalchemy.exc import OperationalError

from vendor_exceptions import ServiceNotConfigured, LambdaTimeOutException, VendorDisabled, VendorExceptions, \
    ApiResponseError, ApiConnectionError
from vendor_vmware_api_client import VmwareApiClient
from vendor_vmware_supported_products import supported_products

from db_client import Database

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
common_service = importlib.import_module("service-common.python.lib.sn_utils")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
sql_logger = logging.getLogger('sqlalchemy.engine')
sql_logger.setLevel(logging.WARNING)


def initiate(*_args, **_kwargs):
    """
       1. get vmware managed products and set the earliest bug date to retrieve
       2. retrieve new bugs
       3. filter bugs based on earliest bug date
    :return:
    """
    # print the event message
    logger.info(f"received event message - {_args[0]}")

    # use a signal handler to set an alarm that will invoke
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm((int(_args[1].get_remaining_time_in_millis() / 1000)) - 1)

    vendor_id = "vmware"
    service_id = "vmware-bug-svc"
    service_name = "VMware Bug Service"
    started_timestamp = datetime.datetime.utcnow()
    execution_service_message = ""
    service_status = "OPERATIONAL"
    service_error = 0
    vmware_api_client = VmwareApiClient(
        vendor_id=vendor_id
    )

    # last executed gap is used to skip managed products processed in the last 6 hours
    utc_now = datetime.datetime.utcnow()
    last_executed_gap = utc_now - datetime.timedelta(hours=6)
    counter = {
        "updated_bugs": 0,
        "skipped_bugs": 0,
        "inserted_bugs": 0,
        "managed_products": 0,
        "new_managed_products": 0,
        "removed_managed_products": 0
    }

    # setup an boto3 SNS client to be used for events or to trigger the bugEventProcessor
    sns_client = boto3.client('sns')
    new_bugs_updates = False

    # ---------------------------------------------------------------------------------------------------------------- #
    #                                    SERVICE NOW EVENT MANAGEMENT CONFIG                                           #
    # ---------------------------------------------------------------------------------------------------------------- #
    event_class = os.environ["EVENT_CLASS"]
    node = os.environ["NODE"]
    resource = _args[1].function_name
    additional_info = f"log_group_name: {_args[1].log_group_name}\nlog_stream_name: {_args[1].log_stream_name}"

    # ---------------------------------------------------------------------------------------------------------------- #
    #                                                 AURORA DB CONFIG                                                 #
    # ---------------------------------------------------------------------------------------------------------------- #
    logger.info(f"environment variables retrieved - {os.environ}")

    managed_products_table = os.environ["MANAGED_PRODUCTS_TABLE"]
    bugs_table = os.environ["BUGS_TABLE"]
    settings_table = os.environ["SETTINGS_TABLE"]
    vendors_table = os.environ["VENDORS_TABLE"]
    service_execution_table = os.environ["SERVICE_EXECUTION_TABLE"]
    services_table = os.environ["SERVICES_TABLE"]

    db_client = ""
    try:
        db_client = Database(
            db_host=os.environ["DB_HOST"],
            db_port=os.environ["DB_PORT"],
            db_user=os.environ["DB_USER"],
            db_password=os.environ["DB_PASS"],
            db_name=os.environ["DB_NAME"],
        )

        db_client.create_session()
        vmware_config = db_client.get_service_config(vendor_id=vendor_id, settings_table=settings_table)
        if not vmware_config:
            message = f"{vendor_id} vendor services are not configured"
            logger.error(message)
            raise ServiceNotConfigured(event_message=message, internal_message=message, service_id=service_id)

        vmware_vendor_settings = db_client.get_vendor_settings(vendor_id=vendor_id, vendors_table=vendors_table)
        if not vmware_vendor_settings:
            message = f"{vendor_id} vendor services are disabled"
            logger.error(message)
            raise VendorDisabled(event_message=message, internal_message=message, vendor_id=vendor_id)

    # ---------------------------------------------------------------------------------------------------------------- #
    #                                                    AUTH PROCESS                                                  #
    # ---------------------------------------------------------------------------------------------------------------- #

        # get generate VMware skyline access token
        # get the vmware user credentials
        vmware_service_cred, tokens, session, client_id = vmware_api_client.get_auth(
            vendor_id=vendor_id, vmware_config=vmware_config.value
        )

    # ---------------------------------------------------------------------------------------------------------------- #
    #                                            INVENTORY AND BUG DISCOVERY                                           #
    # ---------------------------------------------------------------------------------------------------------------- #
        # add the manually inserted CMDB Affected CI Query ( from the UI saved under settings )
        sn_ci_query_base = vmware_config.value.get('snAffectedCIQuery', "")
        # stores managedProduct IDs for managedProducts with active products in vmware skyline
        active_managed_product_ids = []

        # get all organizations managed by the vmware cloud service account
        account_orgs = vmware_api_client.get_account_organizations(service_token=tokens[1])
        orgs_count = len(account_orgs["items"])
        logger.info(
            f"'{vendor_id}' - {orgs_count} organizations found for configured account | updating service config"
        )

        # update the account costumers in DB for UI population
        db_client.update_account_orgs(account_orgs=account_orgs['items'], service_config=vmware_config)

        # only process enabled customers
        enabled_orgs = [x for x in vmware_config.value['accountOrgs'] if not x["disabled"]]
        if not enabled_orgs:
            internal_message = f"'{vendor_id}' - cloud account has no orgs or all customers are disabled in BZ"
            logger.error(internal_message)
            message = f"NetAPP has no customers to process - please visit NetAPP configurations page and select " \
                      f"customers to monitor"
            raise ServiceNotConfigured(
                event_message=message, internal_message=internal_message, service_id=''
            )

        logger.info(
            f"'{vendor_id}' - {len(enabled_orgs)} enabled organizations will be processed | "
            f"{[x['name'] for x in enabled_orgs]}"
        )
        vendor_products = supported_products
        for org in enabled_orgs:
            try:
                org_tokens = vmware_api_client.get_org_tokens(
                    authenticated_session=session, client_id=client_id,
                    vmware_cs_username=vmware_service_cred['username'],
                    org=org
                )
                logger.info(f"'{org['name']}' - validating skyline collectors health")
                vmware_api_client.check_collectors_health(service_token=org_tokens[1], org=org)

                # get hardware inventory from the service API and save vSphere MoRef ID - used in SnCiFilter of the bugs
                inventory = vmware_api_client.get_inventory(
                    org=org, auth_token=org_tokens[0]
                )

                # iterate over inventory, populate products to vendor_products
                for item in inventory["inventory"]:
                    if item["type"].lower() == "vc":
                        vendor_products['vCenter']["hosts"].append(
                            {"id": item["sourceID"].replace("VC:", ""), "version": item["version"],
                             'orgId': org["orgId"], 'orgName': org["name"], "authTokens": org_tokens}
                        )
                        vendor_products['vCenter']["versions"].add(item["version"])

                    clusters = [
                        x for center in item["datacenters"] for x in center["clusters"]
                        if "clusters" in center and center["clusters"]
                    ]
                    hosts = [x for cluster in clusters for x in cluster['hosts'] if cluster.get("hosts", None)]
                    for host in hosts:
                        vendor_products['ESXi']["hosts"].append(
                            {"id": host["id"], 'orgId': org["orgId"], 'orgName': org["name"],
                             "authTokens": org_tokens}
                        )
                        vendor_products['ESXi']["versions"].add(host["version"])
            # handle org specific issues to allow the processing of remaining orgs if exist
            except (ApiResponseError, ApiConnectionError) as e:
                (exception_type, _exception_object, exception_traceback) = sys.exc_info()
                vmware_api_client.generate_error_event(
                    exception_traceback=exception_traceback, exception_type=exception_type, error_type="Operational",
                    error_message=str(e), event_class=event_class, resource=resource, node=node, severity=1,
                    metric_name=e.__class__.__name__, description=traceback.format_exc().replace('"', ""),
                    additional_info=additional_info,
                )
                service_status = "ERROR"
                service_error = 1
                execution_service_message = e.event_message
                continue

        # global last execution, used for new managedProducts or when a managedProduct.lastExecution is null
        last_execution = utc_now - datetime.timedelta(days=int(vmware_config.value['daysBack']))
        for name, product in vendor_products.items():
            logger.info(f"'{name}' - processing supported product")
            managed_product = db_client.get_managed_product(
                managed_products_table=managed_products_table, vendor_id=vendor_id, product_name=name
            )
            product_versions = product["versions"]
            # check status and lastExecution for existing managedProducts
            if managed_product:
                active_managed_product_ids.append(managed_product[0].id)
                logger.info(f"'{name}' - found existing managedProduct")
                counter["managed_products"] += 1
                managed_product = managed_product[0]
                if managed_product.isDisabled:
                    logger.info(f"'{managed_product.name}' - skipping disabled managedProduct")
                    continue

                # skip recently processed managedProducts
                if managed_product.lastExecution and managed_product.lastExecution > last_executed_gap:
                    delta = utc_now - managed_product.lastExecution
                    delta_hours = '{:2.2f}'.format(delta.seconds / 3600)
                    logger.info(
                        f"'{managed_product.name}' - skipping managedProduct processed {delta_hours} hours ago"
                    )
                    continue

                # set last_execution according to managedProduct
                if managed_product.lastExecution:
                    last_execution = managed_product.lastExecution

                db_client.update_managed_product_versions(
                    managed_product=managed_product, versions=product_versions,
                )
            else:
                counter["new_managed_products"] += 1
                managed_product = db_client.create_managed_product(
                    name=product['name'], vendor_id=vendor_id, versions=product_versions,
                    managed_products_table=managed_products_table, service_settings=vmware_config.value
                )
                active_managed_product_ids.append(managed_product.id)

            product_bugs = {}
            # get bugs for each available host
            for host in product["hosts"]:
                version = host.get('version') if isinstance(host, dict) else ""
                skyline_bugs = vmware_api_client.get_skyline_bugs(
                    auth_token=host["authTokens"][1], last_execution=last_execution, prod_id=managed_product.id,
                    morid=host["id"], product_name=managed_product.name, org_id=host["orgId"], org_name=host["orgName"],
                )
                if not skyline_bugs:
                    continue
                # filter bugs by priority
                priorities = {x['vendorPriority']: x["snPriority"] for x in managed_product.vendorPriorities}
                filtered_bugs = vmware_api_client.filter_bugs(
                    bugs=skyline_bugs, host=host, product_name=managed_product.name,
                    product_priorities=priorities
                )
                if not filtered_bugs:
                    continue

                for bug in filtered_bugs:
                    # add version if bug was already processed
                    if version:
                        bug["vendorData"]["versions"].add(version)
                    bug["vendorData"]["morIds"].add(host["id"])

                    if bug["bugId"] not in product_bugs:
                        product_bugs[bug["bugId"]] = bug
                        continue

                    if version:
                        product_bugs[bug["bugId"]]["vendorData"]["versions"].add(version)
                    else:
                        product_bugs[bug["bugId"]]["vendorData"]["morIds"].add(host["id"])

            if product_bugs:
                # add service_now_table and create a snCiFilter with all the hosts/versions
                sorted_product_bugs = sorted(list(product_bugs.values()), key=lambda x: x["bugId"])
                formatted_bugs = vmware_api_client.format_sn_filters(
                    bugs=sorted_product_bugs, managed_product=managed_product,
                    service_now_table=product["service_now_table"], sn_ci_query_base=sn_ci_query_base
                )
                inserts = db_client.insert_bug_updates(
                    bugs=formatted_bugs, bugs_table=bugs_table, product_name=managed_product.name
                )
                if inserts['updated_bugs'] or inserts['inserted_bugs']:
                    new_bugs_updates = True
                counter['updated_bugs'] += inserts['updated_bugs']
                counter['skipped_bugs'] += inserts['skipped_bugs']
                counter['inserted_bugs'] += inserts['inserted_bugs']

            logger.info(
                f"'{managed_product.name}' - sync completed | {counter['inserted_bugs'] + counter['updated_bugs']} "
                f"bugs updates found"
            )
            logger.info(f"'{managed_product.name}' - updating lastExecution")
            setattr(managed_product, 'lastExecution', datetime.datetime.utcnow())
            db_client.conn.commit()
        logger.info(f"'{vendor_id}' - sync complete - {json.dumps(counter)}")

        # remove managedProduct that don't have active products in skyline
        removed_managed_products = db_client.remove_non_active_managed_products(
            bugs_table=bugs_table, managed_products_table=managed_products_table,
            active_managed_product_ids=active_managed_product_ids, vendor_id=vendor_id
        )

        counter['removed_managed_products'] += removed_managed_products
        logger.info(f"'{vendor_id}' - sync complete - {json.dumps(counter)}")

        # on existing bug updates - trigger the bugEventProcessor
        if new_bugs_updates:
            logger.info(
                f"'{vendor_id}' - bug updates found | sending a trigger message to "
                f"{os.environ['BUG_EVENT_PROCESSOR_SERVICE_NAME']}"
            )
            message = json.dumps({'default': f"{vendor_id} bug updates found"})
            sns_client.publish(
                TopicArn=os.environ["SERVICE_SNS_TOPIC_ARN"], Subject="trigger", MessageStructure="json",
                Message=message, MessageAttributes={
                    "service": {"DataType": "String", "StringValue": os.environ['BUG_EVENT_PROCESSOR_SERVICE_NAME']}
                }
            )

        # update execution message
        if counter['inserted_bugs']:
            message = f"{counter['inserted_bugs']} new bugs published"
        elif not counter["managed_products"] and not counter["new_managed_products"]:
            message = 'no managed products were found - check Vmware SkyLine Collectors'
        else:
            message = f"0 new bugs published"

        if not execution_service_message:
            execution_service_message = message

    except (
            Exception, VendorExceptions
    ) as e:
        (exception_type, _exception_object, exception_traceback) = sys.exc_info()
        if isinstance(e, LambdaTimeOutException):
            error_type = "Program"
            severity = 1

        elif isinstance(e, OperationalError):
            error_type = "Operational"
            execution_service_message = "Database connection error - we are working on getting this fixed as soon as " \
                                        "possible"
            severity = 1

        elif isinstance(e, VendorExceptions):
            error_type = "Operational"
            execution_service_message = e.event_message
            severity = 1
        else:
            error_type = "Program"
            severity = 1

        # vendorDisabled exceptions are not considered service error events
        if not isinstance(e, (VendorDisabled, ServiceNotConfigured)):
            # generate an sn event record and send to the sns topic
            service_status = "ERROR"
            service_error = 1
            sns_client = boto3.client('sns')
            event = common_service.sn_event_formatter(
                event_class=event_class, resource=resource, node=node, metric_name=e.__class__.__name__,
                description=traceback.format_exc().replace('"', ""), error_type=error_type, severity=severity,
                additional_info=additional_info,
                logger=logger
            )
            event_string = json.dumps({"default": json.dumps(event)})
            sns_client.publish(
                TopicArn=os.environ["SNS_TOPIC"], Subject="test", MessageStructure="json", Message=event_string
            )
        else:
            service_status = "NOT CONFIGURED"
            service_error = 1
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno
        error_message = {
            "errorType": str(exception_type),
            "errorMsg": str(e),
            "source": "",
            "service": f"{str(filename)} - line {line_number}",
        }
        logger.error(json.dumps(error_message, default=str))
        message = error_message

    vmware_api_client.bug_zero_vendor_status_update(
        service_status=service_status,
        db_client=db_client,
        vendor_id=vendor_id,
        service_execution_table=service_execution_table,
        services_table=services_table,
        service_id=service_id,
        started_at=started_timestamp,
        message=execution_service_message,
        service_name=service_name,
        error=service_error
    )

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
            "function_name": "vmware-bug-svc",
            "log_group_name": "vmware-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000
        })
    )
