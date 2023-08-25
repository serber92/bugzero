# !/usr/bin/env python
"""
   created 2021-09-20
"""
import base64
import datetime
import importlib
import inspect
import json
import logging.config
import os
import re
import signal
import sys
import traceback
from collections import defaultdict

import boto3
from requests.packages import urllib3
from sqlalchemy.exc import OperationalError

from db_client import Database
from vendor_exceptions import VendorDisabled, ServiceNotConfigured, ApiRegexParseError, SnCiFieldMissing, \
    LambdaTimeOutException, VendorExceptions
from vendor_fortinet_api_client import FortinetApiClient
from vendor_fortinet_supported_products import supported_products

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
common_service = importlib.import_module("service-common.python.lib.sn_utils")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
urllib3.disable_warnings()

# modal abbreviation to product name
PRODUCT_MAPPING = {
    "FBL": "FortiADC", "FAD": "FortiADC", "FLG": "FortiAnalyzer", "FL": "FortiAnalyzer", "FAZ": "FortiAnalyzer",
    "FAP": "FortiAP (Access Point)", "FAC": "FortiAuthenticator", "FB": "FortiBridge", "FBG": "FortiBridge",
    "FCH": "FortiCache", "FCM": "FortiCamera", "FCR": "FortiCarrier", "FK": "FortiCarrier", "LK": "FortiCarrier",
    "FCC": "FortiClient", "FCT": "FortiClient", "FCL": "FortiCloud", "FCTL": "FortiController", "FCE": "FortiCore",
    "FDB": "FortiDB (DataBase)", "FI": "FortiDDOS", "FDD": "FortiDDOS", "FNS": "FortiDNS", "FEX": "FortiExtender",
    "FGT": "FortiGate", "FG": "FortiGate", "LF": "FortiGate, Low Encryption BIOS", "FGR": "FortiGate, Ruggedized",
    "FGV": "FortiGate, Voice", "FHV": "FortiHypervisor", "FML": "FortiMail", "FE": "FortiMail", "FMAIL": "FortiMail",
    "FMG": "FortiManager", "FM": "FortiManager", "FSM": "Fortinet Storage Module", "FON": "FortiPhone",
    "FRC": "FortiRecorder", "FSA": "FortiSandbox", "FSC": "FortiScan", "FS": "FortiSwitch", "FT": "FortiSwitchATCA",
    "FSR": "FortiSwitch, Ruggedized", "FTP": "FortiTap", "FTS": "FortiTester", "FTK": "FortiToken",
    "FTM": "FortiToken Mobile", "FVC": "FortiVoice System", "FVE": "FortiVoice, Enterprise",
    "FWN": "FortiWAN Load Balancer", "FV": "FortiWeb", "FWB": "FortiWeb", "FWF": "FortiWiFi", "FW": "FortiWiFi",
    "FWC": "FortiWLC (Wireless Controller)", "FNC": "FortiNAC"
}


def initiate(*_args, **_kwargs):
    """
       Vendor Bug Service
       # keeps the managedProduct versions in sync with existing SN CIs
       1. query sn for supported vendor products and retrieve software versions
       2a. add a managedProduct if not exist
       2b. skip existing managedProducts based on lastExecution timestamp
       2c. update existing managedProduct with current software versions
       3. generate bugzilla search url for managedProduct filters
       4. search bugs
       4. insert bug updates
       5. update lastExecution timestamp
       6a. update services/serviceExecution tables
       6b. send error to sn eventManagement
    :return:
    """
    # print the event message
    logger.info(f"received event message - {_args[0]}")

    # use a signal handler to set an alarm that will invoke
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm((int(_args[1].get_remaining_time_in_millis() / 1000)) - 1)

    # service configuration
    vendor_id = "fortinet"
    service_id = "fortinet-bug-svc"
    service_name = "Fortinet Bug Service"
    service_now_id = "servicenow"
    execution_service_message = ""
    service_status = "OPERATIONAL"
    service_error = 0
    started_timestamp = datetime.datetime.utcnow()
    fortinet_api_client = FortinetApiClient(vendor_id=vendor_id)

    # setup an boto3 SNS client to be used for events or to trigger the bugEventProcessor
    sns_client = boto3.client('sns')

    # last executed gap is used to skip managed products processed in the last 6 hours
    utc_now = datetime.datetime.utcnow()
    last_executed_gap = utc_now - datetime.timedelta(hours=6)
    counter = {
        "updated_bugs": 0,
        "skipped_bugs": 0,
        "inserted_bugs": 0,
        "sn_cmdb_cis_found": 0,
        "managed_products": 0,
        "new_managed_products": 0,
        "removed_managed_products": 0
    }
    # ---------------------------------------------------------------------------------------------------------------- #
    #                                    SERVICE NOW EVENT MANAGEMENT CONFIG                                           #
    # ---------------------------------------------------------------------------------------------------------------- #
    event_class = os.environ["EVENT_CLASS"]
    node = os.environ["NODE"]
    resource = _args[1].function_name
    additional_info = f"log_group_name: {_args[1].log_group_name}\nlog_stream_name: {_args[1].log_stream_name}"

    # -----------------------------------------------------------------------------------------------------------------#
    #                                               AURORA DB CONFIG                                                   #
    # -----------------------------------------------------------------------------------------------------------------#
    managed_products_table = os.environ["MANAGED_PRODUCTS_TABLE"]
    settings_table = os.environ["SETTINGS_TABLE"]
    vendors_table = os.environ["VENDORS_TABLE"]
    service_execution_table = os.environ["SERVICE_EXECUTION_TABLE"]
    services_table = os.environ["SERVICES_TABLE"]
    bugs_table = os.environ["BUGS_TABLE"]
    new_bugs_updates = False

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

        fortinet_config = db_client.get_service_config(vendor_id=vendor_id, settings_table=settings_table)
        if not fortinet_config:
            message = f"{vendor_id} vendor services are not configured"
            logger.error(message)
            raise ServiceNotConfigured(event_message=message, internal_message=message, service_id=service_id)

        fortinet_vendor_settings = db_client.get_vendor_settings(vendor_id=vendor_id, vendors_table=vendors_table)
        if not fortinet_vendor_settings:
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

        sn_auth_credentials = fortinet_api_client.get_aws_secret_value(sn_secret_id)
        sn_auth_token = base64.b64encode(
            f"{sn_auth_credentials['user']}:{sn_auth_credentials['pass']}".encode('ascii')
        ).decode('ascii')
        # ------------------------------------------------------------------------------------------------------------ #
        #                                       MANAGED PRODUCTS SYNC PROCESS                                          #
        # ------------------------------------------------------------------------------------------------------------ #
        vendor_product_types = supported_products
        # stores managedProduct IDs for managedProducts with active products in SN CMDB
        active_managed_product_ids = []
        processed_managed_products = []
        # add the manually inserted CMDB Affected CI Query ( from the UI saved under settings )
        sn_ci_query_base = fortinet_config.value.get('snAffectedCIQuery', "")
        for product_type in vendor_product_types:
            enabled_products = 0

            bugs = list()
            product_versions = dict()
            # get all instances discovered in the product family
            active_cis = fortinet_api_client.sn_sync(
                sn_api_url=sn_api_url, sn_auth_token=sn_auth_token, product_type=product_type,
                sn_ci_query_base=sn_ci_query_base
            )
            if not active_cis:
                continue
            for ci in active_cis:
                counter["sn_cmdb_cis_found"] += 1
                # convert SN short_description to Product Name
                product_name_regex = r"(?<=Fortinet ).*?(?=,|$)"
                try:
                    product_name_container = re.findall(product_name_regex, ci['short_description'])[0]
                    product_name_abbr = product_name_container.split("_")[0]
                    product_modal = product_name_container.split("_")[-1]
                except IndexError as e:
                    raise ApiRegexParseError(
                        url=ci["sn_query_url"],
                        internal_message=f"regex search failed for product name | regex: '{product_name_regex} | "
                                         f"string: '{ci['short_description']}' | field name: 'short_description'",
                        event_message=f"SN CI parse error - we are actively working on a fix",
                        regex=product_name_regex,
                        search_string=ci['short_description']
                    ) from e
                except KeyError as e:
                    raise SnCiFieldMissing(
                        url=ci["sn_query_url"],
                        internal_message=f"SN CI missing a required field - 'short_description' | SN CI sys_id: "
                                         f"'{ci['sys_id']}",
                        event_message=f"SN CI mandatory info missing - we are actively working on a fix",
                        field_name='short_description',
                        ci_sys_id=ci['sys_id']
                    ) from e
                product_name = f"{PRODUCT_MAPPING[product_name_abbr]} {product_name_abbr}-{product_modal}"
                # get the os version
                try:
                    product_firmware_version = re.findall(r"(?<=v)[\d.]+(?=,)", ci['firmware_version'])[0]
                except IndexError as e:
                    raise ApiRegexParseError(
                        url=ci["sn_query_url"],
                        internal_message=f"regex search failed for product os version | regex: '{product_name_regex} | "
                                         f"string: '{ci['firmware_version']}'",
                        event_message=f"SN CI parse error - we are actively working on a fix",
                        regex=product_name_regex,
                        search_string=ci['short_description']
                    ) from e
                except KeyError as e:
                    raise SnCiFieldMissing(
                        url=ci["sn_query_url"],
                        internal_message=f"SN CI missing a required field - 'firmware_version' | SN CI sys_id: "
                                         f"'{ci['sys_id']}",
                        event_message=f"SN CI os version missing - we are actively working on a fix",
                        field_name='firmware_version',
                        ci_sys_id=ci['sys_id']
                    ) from e

                managed_product = db_client.get_managed_product_by_name(
                    product_name=product_name, managed_products_table=managed_products_table, vendor_id=vendor_id
                )
                if managed_product:
                    # add the product to the list of active products
                    active_managed_product_ids.append(managed_product.id)
                    counter["managed_products"] += 1
                    index = managed_product[0][0]
                    managed_product = managed_product[0][-1]
                    if managed_product.isDisabled:
                        managed_products.pop(index)
                        logger.info(f"'{managed_product.name}' - skipping disabled product")
                        continue
                    if managed_product.lastExecution and managed_product.lastExecution > last_executed_gap:
                        managed_products.pop(index)
                        delta = utc_now - managed_product.lastExecution
                        delta_hours = '{:2.2f}'.format(delta.seconds / 3600)
                        logger.info(
                            f"'{managed_product.name}' - skipping managedProduct processed {delta_hours} hours ago"
                        )
                        continue
                else:
                    managed_product = db_client.create_managed_product(
                        name=product_name, vendor_id=vendor_id, versions=[product_firmware_version],
                        managed_products_table=managed_products_table, product_type_name=product_type['type'],
                        service_settings=fortinet_config.value
                    )
                    counter["new_managed_products"] += 1
                    # add the product to the list of active products
                    active_managed_product_ids.append(managed_product.id)
                if managed_product.id not in versions_by_managed_products:
                    versions_by_managed_products[managed_product.id] = {
                        "versions": {product_firmware_version}, "managed_product": managed_product
                    }
                else:
                    versions_by_managed_products[managed_product.id]["versions"].append(product_firmware_version)

                enabled_products = 1
                counter["managed_products"] += 1
                processed_managed_products.append(managed_product)

        # ------------------------------------------------------------------------------------------------------------ #
        #                                              BUG SERVICE                                                     #
        # ------------------------------------------------------------------------------------------------------------ #
            # skip if none of the product_type products are enabled or ready to be processed
            if not enabled_products or not versions_by_managed_products.keys():
                continue

            # get all the release notes urls for a given product
            for product in product_type["products"]:
                release_notes_urls = fortinet_api_client.generate_release_notes_urls(
                    product_name=product['name'], product_slug_name=product["slug"]
                )
                if release_notes_urls:
                    version_bugs = fortinet_api_client.release_notes_download_manager(
                        release_notes_urls=release_notes_urls, product_name=product["name"]
                    )

                    if not version_bugs:
                        continue
                    bugs.extend(version_bugs)
            # bugs found, consolidate known and resolved information for release notes issues to one bug entry
            consolidated_bugs = fortinet_api_client.consolidate_bugs(bugs=bugs)

            # filter to bugs that are relevant to the versions the CIs are running
            for version, managed_product in product_versions.items():
                excluded_bugs = []
                version_bugs = []
                status_bugs = []
                formatted_bugs = list()
                for x in consolidated_bugs:
                    if version in x["knownAffectedReleases"]:
                        version_bugs.append(x)
                    else:
                        excluded_bugs.append(x)

                for x in version_bugs:
                    # filter to bugs based on the supported managedProduct vendorStatuses
                    if x["status"] in managed_product.vendorStatuses:
                        status_bugs.append(x)
                    else:
                        excluded_bugs.append(x)

                consolidated_bugs = excluded_bugs
                # format filtered bugs to be inserted to the bugs table
                if bugs:
                    status_bugs = fortinet_api_client.format_bug_entry(
                        managed_product=managed_product["managed_product"], bugs=bugs, sn_ci_filter=sn_ci_query_base,
                        sn_ci_table=product_type["service_now_ci_table"]
                    )
                    formatted_bugs.extend(status_bugs)

                # insert formatted bugs
                if formatted_bugs:
                    count = db_client.insert_bug_updates(bugs=formatted_bugs, bugs_table=bugs_table)
                    if count.get('updated_bugs') or count.get('inserted_bugs'):
                        new_bugs_updates = True
                    counter["updated_bugs"] += count["updated_bugs"]
                    counter["inserted_bugs"] += count["inserted_bugs"]
                    counter["skipped_bugs"] += count["skipped_bugs"]
                    logger.info(
                        f"'{managed_product['managed_product'].name}' - sync completed | {json.dumps(count)}"
                    )
                else:
                    logger.info(f"'{managed_product['managed_product'].name}' - sync completed | 0 new bugs found")
                    db_client.conn.commit()

            managed_product_os_version_map = defaultdict(list)
            for key, value in product_versions.items():
                managed_product_os_version_map[value].append(key)
            for managed_product, versions in managed_product_os_version_map.items():
                db_client.update_managed_product_versions(managed_product=managed_product, versions=versions)

            for m in processed_managed_products:
                logger.info(f"'{m.name}' - updating lastExecution")
                setattr(m, 'lastExecution', datetime.datetime.utcnow())

        db_client.conn.commit()

        # remove managedProduct and linked bugs that don't have an active CMDB CI
        # ( are not included in active_managed_product_ids )
        removed_managed_products = db_client.remove_non_active_managed_products(
            bugs_table=bugs_table, managed_products_table=managed_products_table,
            active_managed_product_ids=active_managed_product_ids, vendor_id=vendor_id
        )

        counter['removed_managed_products'] += removed_managed_products
        logger.info(f"'{vendor_id}' sync completed - {json.dumps(counter)}")

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
        if counter["sn_cmdb_cis_found"]:
            message = f"{counter['inserted_bugs']} new bugs published"
        elif not counter["managed_products"]:
            message = 'no active SN CIs matching enabled managed products were found'
        else:
            message = f"0 new bugs published"

        execution_service_message = message

    except (
            Exception, VendorExceptions
    ) as e:
        (exception_type, _exception_object, exception_traceback) = sys.exc_info()
        if isinstance(e, OperationalError):
            error_type = "Operational"
            execution_service_message = "Database connection error - we are working on getting this fixed as soon as " \
                                        "possible"
            severity = 1

        elif isinstance(e, LambdaTimeOutException):
            error_type = "Program"
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

    fortinet_api_client.bug_zero_vendor_status_update(
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
            "function_name": "fortinet-bug-svc",
            "log_group_name": "fortinet-bug-svc",
            "get_remaining_time_in_millis": lambda *_args, **_kwargs: 9000000
        })
    )
