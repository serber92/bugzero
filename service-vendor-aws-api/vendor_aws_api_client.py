#!/usr/bin/env python3
"""
created 2021-12-14
"""
import base64
import datetime
import importlib
import inspect
import json
import logging.config
import os
import sys

import boto3
import pytest
import pytz
from botocore.exceptions import ClientError
from requests.packages import urllib3

from download_manager import download_instance
from vendor_exceptions import ApiResponseError, ApiConnectionError

urllib3.disable_warnings()
logger = logging.getLogger()

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
common_service = importlib.import_module("service-common.python.lib.sn_utils")

EVENT_TYPE_MAP = {
    "Issue": "issue",
    "Account Notification": "accountNotification",
    "Scheduled Change": "scheduledChange"
}
EVENT_TYPE_REVERSE = {
    "issue": "Issue",
    "accountNotification": "Account Notification",
    "scheduledChange": "Scheduled Change"
}


class AwsApiClient:
    """
    - a class with methods to extract data from aws health and group resources api, work with Aurora Serverless
      MySQL tables
    - errors are logged and reported as service now events
    """
    @pytest.mark.skip(reason="class initializer - nothing to test")
    def __init__(
            self,
            vendor_id,
    ):  # pragma: no cover
        """

        :param vendor_id:
        """
        # ------------------------------------------------------------------------------------------------------------ #
        #                                                   GLOBAL VARIABLES                                           #
        # ------------------------------------------------------------------------------------------------------------ #
        self.bug_ids = set()
        self.bugs = []
        self.kb_entries_retrieved = 0
        self.total_kb_entries = 0
        self.kb_info_parse_errors = 0
        self.kb_failed_urls = []
        self.logger = logger
        self.vendor_id = vendor_id
        self.sn_table = ""
        self.sts_client = boto3.client('sts')
        self.secret_manager_client = boto3.Session().client("secretsmanager")

    def bug_zero_vendor_status_update(
            self, db_client, started_at, services_table, service_execution_table, service_status, vendor_id,
            service_id, service_name, error=0, message=""
    ):
        """
        update services and serviceExecutions tables with information about a service execution
        :param services_table:
        :param service_execution_table:
        :param service_id:
        :param service_name:
        :param started_at:
        :param vendor_id:
        :param db_client:
        :param error:
        :param message:
        :param service_status:
        :return:
        """

        self.logger.info(f"updating - '{service_execution_table}' and '{services_table}'")
        now_utc = datetime.datetime.utcnow()

        # update the service status
        service_entry = db_client.conn.query(
            db_client.base.classes[services_table]
        ).filter(
            db_client.base.classes[services_table].id == [
                service_id
            ]
        ).first()
        if not service_entry:
            service_entry = {
                "name": service_name,
                "status": service_status,
                "message": message,
                "lastExecution": started_at,
                "lastSuccess": now_utc if not error else None,
                "lastError": now_utc if error else None,
                "enabled": 1,
                "createdAt": now_utc,
                "updatedAt": now_utc,
                "vendorId": self.vendor_id,
                "id": service_id
            }

            service_entry = db_client.base.classes[services_table](**service_entry)
            db_client.conn.add(service_entry)

        else:
            setattr(service_entry, "status", service_status)
            setattr(service_entry, "lastExecution", started_at)
            setattr(service_entry, "message", message)

            # error fields
            if error:
                setattr(service_entry, "lastError", now_utc)

            else:
                setattr(service_entry, "lastSuccess", now_utc)

        # new service execution entry
        new_execution_entry = {
            "endedAt": now_utc,
            "startedAt": started_at,
            "createdAt": now_utc,
            "updatedAt": now_utc,
            "vendorId": vendor_id,
            "serviceId": service_id,
            "error": error,
            "errorMessage": message

        }

        new_execution_entry = db_client.base.classes[service_execution_table](
            **new_execution_entry
        )
        db_client.conn.add(new_execution_entry)
        db_client.conn.commit()

    def get_aws_secret_value(self, secret_name):
        """
        retrieve a secret value from AWS Secrets Manager for a secret name
        :param secret_name:
        :return:
        """
        try:
            get_secret_value_response = self.secret_manager_client.get_secret_value(
                SecretId=secret_name
            )
            if "SecretString" in get_secret_value_response:
                secret = json.loads(get_secret_value_response["SecretString"])
                return secret
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response["SecretBinary"]
            )
            return decoded_binary_secret
        except ClientError as e:
            (exception_type, _exception_object, exception_traceback) = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            error = {
                "url": "",
                "errorType": str(exception_type),
                "errorMsg": str(e),
                "source": "",
                "service": f"{str(filename)} - line {line_number}",
            }
            internal_messages = f"'{self.vendor_id}' - AWS SecretManager error | {json.dumps(error)}"
            event_message = f"'{self.vendor_id}' - AWS API error | we are actively working on a fix"
            self.logger.error(internal_messages)
            raise ApiConnectionError(
                event_message=event_message, internal_message=internal_messages, url=""
            ) from e

    def format_bug_entry(self, health_event, managed_product, last_execution, active_regions):
        """
        format product bugs to bz bug entries
        filter out events based on inventory status:
            a. eventScopeCode
            b. vendorPriority
            c. active regions
            d. managed product last execution
        :param health_event:
        :param managed_product:
        :param last_execution:
        :param active_regions:
        :return:
        """
        formatted_entry = dict()
        verified = True

        # skip events based on eventScopeCodes
        event_scopes = [x.replace(" ", "_").upper() for x in managed_product.vendorData["vendorEventScopes"]]
        if health_event["event"]["eventScopeCode"] not in event_scopes:
            verified = False
        # skip events based on priority
        managed_product_priorities_map = [EVENT_TYPE_MAP[x['vendorPriority']] for x in managed_product.vendorPriorities]
        if not [
            x for x in managed_product_priorities_map
            if x == health_event["event"]['eventTypeCategory']
        ]:
            verified = False
        # skip events based on active region
        if health_event["event"]['region'] not in active_regions:
            verified = False
        # skip events based on last_execution
        event_last_update_utc = health_event['event']['lastUpdatedTime'].astimezone(pytz.utc)
        if last_execution.astimezone(pytz.utc) > (event_last_update_utc - datetime.timedelta(days=2)):
            verified = False
        # skip events based on status
        if not health_event["event"]["statusCode"].title() in managed_product.vendorStatuses:
            return False

        if not verified:
            return False
        formatted_entry["bugId"] = str(health_event['event']['arn'].split('/')[-1]).rsplit('_', maxsplit=1)[-1]
        formatted_entry["description"] = health_event["eventDescription"]['latestDescription'].strip()
        formatted_entry["vendorLastUpdatedDate"] = health_event['event']['lastUpdatedTime']
        formatted_entry["vendorCreatedDate"] = health_event['event']['startTime']
        formatted_entry["knownAffectedReleases"] = managed_product.name
        formatted_entry["summary"] = f"{health_event['event']['eventTypeCode'].replace('_',' ').title()} - " \
                                     f"{health_event['event']['region']} - " \
                                     f"{health_event['event']['eventScopeCode'].title().replace('_',' ')} " \
                                     f"{health_event['event']['eventTypeCategory'].title()} - " \
                                     f"{health_event['event']['arn'].split('/')[-1]}"
        formatted_entry["bugUrl"] = f"https://phd.aws.amazon.com/phd/home#/event-log?eventID=" \
                                    f"{health_event['event']['arn']}"

        formatted_entry["priority"] = EVENT_TYPE_REVERSE[health_event['event']['eventTypeCategory']]
        formatted_entry["managedProductId"] = managed_product.id
        formatted_entry["status"] = health_event['event']['statusCode'].title()
        formatted_entry["snCiFilter"] = "install_status=1^operational_status=1" \
                                        "?sysparm_query=status=In%20Production^manufacturer.name=AWS"
        formatted_entry["snCiTable"] = "cmdb_model"
        formatted_entry["vendorId"] = self.vendor_id
        formatted_entry["vendorData"] = {}

        return formatted_entry

    @staticmethod
    def timestamp_format(time_str):
        """
        convert timedate strings to timedate objects
        :param time_str:
        :return:
        """
        # max 6 digit micro second
        known_formats = [
            "%Y-%m-%d", "%B %d, %Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ",
            "%a, %d %b %Y %H:%M:%S Z", "%a, %d %b %Y %H:%M:%SZ"
        ]
        fmt_time = ""
        for _i, fmt in enumerate(known_formats):
            check_string = time_str
            try:
                fmt_time = datetime.datetime.strptime(check_string, fmt)
                break
            except ValueError:
                continue
        if fmt_time:
            return fmt_time
        return time_str

    def sn_sync(self, query_product, sn_api_url, sn_auth_token):
        """
        keep managed products software version up to date with the correlating instances in the SN instance
        run sn queries to find product version in the SN instance
        :param sn_api_url:
        :param sn_auth_token:
        :param query_product:
        :return:
        """
        sn_query = f"?sysparm_query={query_product['sysparm_query']}"
        sn_query_url = f"{sn_api_url}/api/now/table/{query_product['service_now_table']}{sn_query}"
        response = download_instance(
            link=sn_query_url,
            headers={"Authorization": f"Basic {sn_auth_token}"}
        )
        if not response:
            self.logger.error(f"SN API connection error - {sn_query_url}")
            raise ApiConnectionError(
                url=sn_query_url, internal_message="SN API connection error",
                event_message="a connection to ServiceNow could not be established - check ServiceNow settings"
            )
        try:
            count = int(response.headers["x-total-count"])
        except KeyError as e:
            raise ApiResponseError(
                url=sn_query_url, internal_message="missing 'x-total-count' in sn query response",
                event_message="ServiceNow query returned a malformed response - check ServiceNow settings"
            ) from e
        if count:
            self.logger.info(
                f"'{query_product['name']}' - {count} SN package(s) found in table "
                f"'{query_product['service_now_table']}'"
            )
            try:
                instances = json.loads(response.text)["result"]
            except json.JSONDecodeError as e:
                raise ApiResponseError(
                    url=sn_query_url, internal_message="error parsing serviceNow response - check url",
                    event_message="ServiceNow query returned a malformed response - check ServiceNow settings"
                ) from e
            # populate query url
            map(lambda x: setattr(x, 'sn_query_url', sn_query_url), instances)
            return instances
        self.logger.info(
            f"'{query_product['name']}' - No SN package(s) found in table '{query_product['service_now_table']}' | "
            f"{sn_query_url}"
        )
        return []

    def get_service_usage_regions(self, cost_explorer_client, supported_services):
        """
        return the service usage amount per service grouped by regions
        :param supported_services:
        :param cost_explorer_client:
        :return:
        """
        self.logger.info(f"'{self.vendor_id}' - looking for services usage activity")
        response = cost_explorer_client.get_cost_and_usage(
            TimePeriod={
                'Start': (datetime.datetime.utcnow() - datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
                'End': (datetime.datetime.utcnow() - datetime.timedelta(hours=4)).strftime("%Y-%m-%d")

            },
            Granularity='MONTHLY',
            Metrics=['UsageQuantity'],
            # Filter={
            #     'Dimensions': {
            #         'Key': 'SERVICE',
            #         'Values': [
            #             service_name,
            #         ]
            #     }
            # },
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                },
                {
                    'Type': 'DIMENSION',
                    'Key': 'REGION'
                }
            ]
        )
        usage_by_product_by_region = {}
        for service in response['ResultsByTime'][-1]["Groups"]:
            service_name = service["Keys"][0]
            service_config = [x for x in supported_services if x["service_name"] == service_name]
            if service_config:
                min_usage_threshold = service_config[0]['min_usage_threshold']
                region = service["Keys"][1]
                if service_name in usage_by_product_by_region:
                    if float(service["Metrics"]['UsageQuantity']["Amount"]) > min_usage_threshold:
                        usage_by_product_by_region[service_name][region] = service["Metrics"]['UsageQuantity']["Amount"]
                else:
                    usage_by_product_by_region[service_name] = {
                        region:  service["Metrics"]['UsageQuantity']["Amount"]
                    }

        return usage_by_product_by_region
