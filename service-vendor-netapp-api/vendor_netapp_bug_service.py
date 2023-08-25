#!/usr/bin/env python3
"""
created 2021-11-15
"""
import base64
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

from db_client import Database
from vendor_exceptions import VendorDisabled, ServiceNotConfigured, VendorExceptions, LambdaTimeOutException, \
    ApiResponseError, ApiConnectionError
from vendor_netapp_api_client import NetAppApiClient

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
       1. authenticate netapp client
       2. get inventory from NetApp API
       3. create/update managedProducts for supported products
       4. retrieve bugs for managedProducts from NetApp API
       5. filter bugs based on status, priority, bugsDaysBack
       6. upsert bugs
    :return:
    """
    # log event message
    logger.info(f"received event message - {json.dumps(_args[0])}")
    # use a signal handler to set an alarm that will invoke
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm((int(_args[1].get_remaining_time_in_millis() / 1000)) - 1)
    vendor_id = "netapp"
    service_id = "netapp-bug-svc"
    service_name = "NetApp Bug Service"
    service_now_id = "servicenow"
    execution_service_message = ""
    service_status = "OPERATIONAL"
    service_error = 0
    started_timestamp = datetime.datetime.utcnow()
    netapp_api_client = NetAppApiClient(
        vendor_id=vendor_id
    )

    # setup an boto3 SNS client to be used for events or to trigger the bugEventProcessor
    sns_client = boto3.client('sns')

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
    utc_now = datetime.datetime.utcnow()
    last_executed_gap = utc_now - datetime.timedelta(hours=6)
    managed_products_table = os.environ["MANAGED_PRODUCTS_TABLE"]
    bugs_table = os.environ["BUGS_TABLE"]
    settings_table = os.environ["SETTINGS_TABLE"]
    vendors_table = os.environ["VENDORS_TABLE"]
    service_execution_table = os.environ["SERVICE_EXECUTION_TABLE"]
    services_table = os.environ["SERVICES_TABLE"]
    # create a db session
    db_client = ""
    try:
        db_client = Database(
            db_host=os.environ["DB_HOST"],
            db_port=os.environ["DB_PORT"],
            db_user=os.environ["DB_USER"],
            db_password=os.environ["DB_PASS"],
            db_name=os.environ["DB_NAME"]
        )
        db_client.create_session()

        netapp_config = db_client.get_service_config(vendor_id=vendor_id, settings_table=settings_table)
        if not netapp_config:
            message = f"{vendor_id} vendor services are not configured"
            logger.error(message)
            raise ServiceNotConfigured(event_message=message, internal_message=message, service_id=service_id)

        netapp_vendor_settings = db_client.get_vendor_settings(vendor_id=vendor_id, vendors_table=vendors_table)
        if not netapp_vendor_settings:
            message = f"{vendor_id} vendor services are disabled"
            logger.error(message)
            raise VendorDisabled(event_message=message, internal_message=message, vendor_id=vendor_id)

        # get service now settings for queries
        service_now_settings = db_client.get_service_config(vendor_id=service_now_id, settings_table=settings_table)
        if not service_now_settings:  # pragma: no cover - tested above
            message = f"ServiceNow connection info is missing - please check ServiceNow configurations page"
            internal_message = f"{service_now_id} does not exist in '{settings_table}' - can't start sync service"
            logger.error(internal_message)
            raise ServiceNotConfigured(
                event_message=message, internal_message=internal_message, service_id=service_now_id
            )

        # sn settings should include two populated fields
        sn_api_url = service_now_settings.value.get("snApiUrl")
        sn_secret_id = service_now_settings.value.get("secretId")

        if not sn_api_url or not sn_secret_id:
            internal_message = f"'{service_now_id}' config missing snApiUrl/secretId in '{settings_table}' - " \
                               f"can't start sync"
            logger.error(internal_message)
            message = f"ServiceNow connection info is missing - please check ServiceNow configurations page"
            raise ServiceNotConfigured(
                event_message=message, internal_message=internal_message, service_id=service_now_id
            )

        sn_auth_credentials = netapp_api_client.get_aws_secret_value(
            secret_name=sn_secret_id, secret_fields=[]
        )
        sn_auth_token = base64.b64encode(
            f"{sn_auth_credentials['user']}:{sn_auth_credentials['pass']}".encode('ascii')
        ).decode('ascii')
        if not sn_auth_token:
            pass

    # ---------------------------------------------------------------------------------------------------------------- #
    #                                                VENDOR AUTH PROCESS                                               #
    # ---------------------------------------------------------------------------------------------------------------- #
        # get netapp mysupport credentials from AWS secrets manager
        if not netapp_config.value.get("secretId", None):
            internal_message = f"'{vendor_id}' config missing refresh - vendor authentication cannot" \
                               f" proceed"
            logger.error(internal_message)
            message = f"NetAPP ActiveIQ refresh token is missing - please check NetAPP configurations page"
            raise ServiceNotConfigured(
                event_message=message, internal_message=internal_message, service_id=service_now_id
            )

        refresh_token = netapp_api_client.get_aws_secret_value(
            secret_name=netapp_config.value["secretId"], secret_fields=["refreshToken"]
        )["refreshToken"]

        # generate access token for Active IQ api accesses
        api_tokens = netapp_api_client.generate_api_tokens_v2(
            refresh_token=refresh_token
        )

        secret_value = {"refreshToken": api_tokens["refresh_token"]}
        netapp_api_client.update_aws_secret(
            value=secret_value, secret_name=netapp_config.value['secretId']
        )

    # ---------------------------------------------------------------------------------------------------------------- #
    #                                                MANAGED PRODUCT SYNC                                              #
    # ---------------------------------------------------------------------------------------------------------------- #
        # stores managedProduct IDs for managedProducts with active CIs in SN CMDB
        active_managed_product_ids = []

        # add the manually inserted CMDB Affected CI Query ( from the UI saved under settings )
        sn_ci_query_base = netapp_config.value.get('snAffectedCIQuery', "")
        # an active IQ account has multiple customers
        customers_endpoint = "https://api.activeiq.netapp.com/v1/system/list/level/customer"
        logger.info(f"'{vendor_id}' - getting Active QI customer IDs | {customers_endpoint}")
        account_customers = netapp_api_client.consume_api(
            auth_token=api_tokens["access_token"], endpoint_url=customers_endpoint
        )
        customers_count = len(account_customers["customers"]["list"])
        logger.info(
            f"'{vendor_id}' - {customers_count} customers found for configured account | updating vendor settings"
        )

        # update the account costumers in DB for UI population
        db_client.update_account_customers(account_customers=account_customers, service_config=netapp_config)

        # only process enabled customers
        enabled_customers = [x for x in netapp_config.value['activeIqCustomers'] if not x["disabled"]]
        if not enabled_customers:
            internal_message = f"'{vendor_id}' - Active IQ account has no customers or all customers are disabled in BZ"
            logger.error(internal_message)
            message = f"NetAPP has no customers to process - please visit NetAPP configurations page and select " \
                      f"customers to monitor"
            raise ServiceNotConfigured(
                event_message=message, internal_message=internal_message, service_id=service_now_id
            )

        logger.info(
            f"'{vendor_id}' - {len(enabled_customers)} enabled customers will be processed | "
            f"{[x['customerName'] for x in enabled_customers]}"
        )

        # get existing managed products
        managed_products = db_client.get_managed_products(
            managed_products_table=managed_products_table, vendor_id=vendor_id
        )

        # get all the systems from enabled customers and add to inventory_products
        inventory_products = {}
        for customer in enabled_customers:
            systems_endpoint = f"https://api.activeiq.netapp.com/v1/systemList/aggregate/level/customer/id/" \
                               f"{customer['customerId']}"
            logger.info(f"'{customer['customerName']}' - getting customer systems | {systems_endpoint}")
            # enable event error generation for individual orgs
            try:
                customer_systems = netapp_api_client.consume_api(
                    auth_token=api_tokens["access_token"], endpoint_url=systems_endpoint,
                    org_name=customer['customerName']
                )
                if not customer_systems['results']:
                    logger.error(
                        f"'{vendor_id}' - API connection error | {systems_endpoint} - {customer['customerName']}"
                    )
                    raise ApiResponseError(
                        url=systems_endpoint,
                        internal_message=f"vendor API response error | {customer['customerName']}",
                        event_message=f"connection to vendor api failed | {customer['customerName']}"
                    )
            except (ApiResponseError, ApiConnectionError) as e:
                (exception_type, _exception_object, exception_traceback) = sys.exc_info()
                netapp_api_client.generate_error_event(
                    exception_traceback=exception_traceback, exception_type=exception_type, error_type="Operational",
                    error_message=str(e), event_class=event_class, resource=resource, node=node, severity=1,
                    metric_name=e.__class__.__name__, description=traceback.format_exc().replace('"', ""),
                    additional_info=additional_info,
                )
                service_status = "ERROR"
                service_error = 1
                execution_service_message = e.event_message
                continue

            for system in customer_systems['results']:
                if not system.get("model"):
                    continue
                netapp_api_client.account_systems[system['system_id']] = system
                if system["model"] not in inventory_products:
                    inventory_products[system["model"]] = {system["version"]}
                else:
                    inventory_products[system["model"]].add(system["version"])

        # iterate inventory_products and create/update managed products
        new_managed_products = []
        to_process_managed_products = []
        for product_model, versions in inventory_products.items():
            versions = sorted(versions)
            existing_managed_product = [
                x for x in managed_products if product_model == x.vendorData['vendorProductModelId']
            ]
            if not existing_managed_product:
                managed_product = db_client.create_managed_product(
                    name=f"NetApp {product_model}", model=product_model, versions=versions,
                    vendor_id=vendor_id, managed_products_table=managed_products_table,
                    service_settings=netapp_config.value
                )
                new_managed_products.append(managed_product)
                active_managed_product_ids.append(managed_product.id)
            else:
                managed_product = existing_managed_product[0]
                active_managed_product_ids.append(managed_product.id)
                if managed_product.isDisabled:
                    logger.info(f"'{managed_product.name}' - skipping disabled product")
                    continue

                if managed_product.lastExecution and managed_product.lastExecution > last_executed_gap:
                    delta = utc_now - managed_product.lastExecution
                    delta_hours = '{:2.2f}'.format(delta.seconds / 3600)
                    logger.info(
                        f"'{managed_product.name}' - skipping managedProduct processed {delta_hours} hours ago"
                    )
                    continue

                db_client.update_managed_product_versions(existing_managed_product[0], versions=versions)
            to_process_managed_products.append(managed_product)

        if new_managed_products:
            logger.info(
                f"'{vendor_id}' - {len(new_managed_products)} new managed products created | "
                f"{json.dumps([x.name for x in new_managed_products])}"
            )

    # ---------------------------------------------------------------------------------------------------------------- #
    #                                                  BUG SERVICE                                                     #
    # ---------------------------------------------------------------------------------------------------------------- #
        bugs = dict()
        if to_process_managed_products:
            logger.info(
                f"'{vendor_id}' - processing enabled account customers | {json.dumps(enabled_customers, default=str)}"
            )

            # iterate over the enabled account customers and look for risks
            for customer in enabled_customers:
                customer_id = customer['customerId']
                customer_name = customer['customerName']

                # get customer risks
                # risks_endpoint = f"https://api.activeiq.netapp.com/v2/health/risks?customer={customer_id}&limit=10"
                customer_risks = list()
                step = 100
                limit = step
                start = 1
                page_count = 1
                while True:
                    risks_endpoint = f"https://api.activeiq.netapp.com/v1/wellness2/risks/level/customer/id/" \
                                     f"{customer_id}/impactarea/all?start={start}&limit={step}" \
                                     f"&sortColumn=impactLevel&sortOrder=desc"
                    logger.info(f"'{customer_name}' - getting customer risks page {page_count} | {risks_endpoint}")
                    # enable event error generation for individual orgs
                    try:
                        data = netapp_api_client.consume_api(
                            auth_token=api_tokens["access_token"], endpoint_url=risks_endpoint,
                            org_name=customer_name
                        )
                    except (ApiResponseError, ApiConnectionError) as e:
                        (exception_type, _exception_object, exception_traceback) = sys.exc_info()
                        netapp_api_client.generate_error_event(
                            exception_traceback=exception_traceback, exception_type=exception_type,
                            error_type="Operational", error_message=str(e), event_class=event_class, resource=resource,
                            node=node, severity=1, metric_name=e.__class__.__name__, additional_info=additional_info,
                            description=traceback.format_exc().replace('"', ""),
                        )
                        service_status = "ERROR"
                        service_error = 1
                        execution_service_message = e.event_message
                        continue

                    risks = data["results"]['risks']
                    total_risks = data["results"]['totalRisksCount']
                    customer_risks.extend(risks)
                    if total_risks > limit:
                        page_count += 1
                        limit += step
                        start += step
                        continue
                    break
                # filter risks to those include a bug reference
                filtered_risks = netapp_api_client.filter_risks(
                    risks=customer_risks, customer_name=customer_name
                )

                # merge risk and bug data into a formatted bug entry
                formatted_bugs = netapp_api_client.format_bug_entries(
                    bugs=filtered_risks, customer_name=customer_name, managed_products=to_process_managed_products,
                )

                # if bug id already exists add unique cis serial number
                for bug in formatted_bugs:
                    if bug["bugId"] not in bugs:
                        bugs[bug["bugId"]] = bug
                        continue

                    for x in bug["affectedSerialNos"]:
                        bugs[bug["bugId"]]['affectedSerialNos'].add(x)
                    for x in bug["knownAffectedReleases"]:
                        bugs[bug["bugId"]]['knownAffectedReleases'].add(x)

            # convert bug dict to list
            bugs_list = list(bugs.values())
            bug_updates = db_client.insert_bug_updates(
                bugs=bugs_list, bugs_table=bugs_table, sn_ci_query_base=sn_ci_query_base
            )

            # on existing bug updates - trigger the bugEventProcessor
            if bug_updates['inserted_bugs'] or bug_updates['updated_bugs']:
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

            # update lastExecuted for managedProducts
            for m in to_process_managed_products:
                setattr(m, 'lastExecution', datetime.datetime.utcnow())
            db_client.conn.commit()

            # remove managedProduct and linked bugs that don't have an active CMDB CI
            db_client.remove_non_active_managed_products(
                bugs_table=bugs_table, managed_products_table=managed_products_table,
                active_managed_product_ids=active_managed_product_ids, vendor_id=vendor_id
            )

            execution_service_message = f"{bug_updates['inserted_bugs']} bug(s) published"
            bug_updates["new_managed_products"] = len(new_managed_products)
            message = bug_updates
        else:
            execution_service_message = f"no bug updates found"
            message = execution_service_message

    except (
            Exception, LambdaTimeOutException, VendorExceptions
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

    netapp_api_client.bug_zero_vendor_status_update(
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
    mock_event = {
        "password": "",
        "username": "",
    }
    initiate(
        '',
        type("MockContext", (object,), {
            "log_stream_name": "test",
            "function_name": "netapp-bug-svc",
            "log_group_name": "netapp-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 900000

        })
    )
