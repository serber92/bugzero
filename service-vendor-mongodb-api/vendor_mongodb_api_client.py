#!/usr/bin/env python3

"""
created 2021-04-27
"""
import base64
import datetime
import importlib
import inspect
import json
import logging.config
import os
import re
import sys
from urllib.parse import quote_plus

import boto3
from botocore.exceptions import ClientError
from lxml import etree
from requests.packages import urllib3
from sqlalchemy import or_
from xmljson import Yahoo

from download_manager import download_instance
from vendor_exceptions import ApiResponseError, ApiConnectionError

urllib3.disable_warnings()
logger = logging.getLogger()

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
common_service = importlib.import_module("service-common.python.lib.sn_utils")


class MongoApiClient:
    """
    - a class with methods to consume MongoJiraAPI, work with Aurora Serverless MySQL tables
    - errors are logged and reported as service now events
    """

    def __init__(
            self,
            vendor_id,
            service_now_ci_table="cmdb_ci_db_mongodb_instance",
    ):
        """

        :param vendor_id:
        :param service_now_ci_table:
        """
        # ------------------------------------------------------------------------------------------------------------ #
        #                                                   GLOBAL VARIABLES                                           #
        # ------------------------------------------------------------------------------------------------------------ #
        self.bug_ids = set()
        self.dedup_count = 0
        self.bugs = dict()
        self.logger = logger
        self.service_now_ci_table = service_now_ci_table
        self.sn_query_cache = {}
        self.sn_versions = []
        self.vendor_id = vendor_id
        self.thread_error_tracker = 0
        self.issues_endpoint_url = \
            "https://jira.mongodb.org/sr/jira.issueviews:searchrequest-xml/temp/SearchRequest.xml?" \
            "jqlQuery={}&" \
            "tempMax=100000"
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

        self.logger.info(f"'{self.vendor_id}' - updating tables '{service_execution_table}' and '{services_table}'")
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

    @staticmethod
    def create_jql_query(search_filter_map):
        """
        generate a JQL query for bug retrieval based on passed in field operators and values
        :param search_filter_map:
        :return:
        """
        query = ""
        for i, (field_name, definition) in enumerate(search_filter_map.items()):
            if not definition['value']:
                continue
            addition = ""
            if i != 0:
                addition = " AND "

            if definition["operator"] in ["=", ">=", "<="]:
                query += f"{addition}{field_name} {definition['operator']} {definition['value']}"

            elif definition["operator"] == "in":
                in_group = ['"{}"'.format(x) for x in definition['value']]
                in_group = f"({', '.join(in_group)})"
                query += f"{addition}{field_name} {definition['operator']} {in_group}"

            elif definition["operator"] == "order":
                query += f" ORDER BY {definition['value']} {definition['direction']}"
        return query

    def get_bugs(self, jql_statement, product_name):
        """
        generate a consume request to get bugs that were resolved within the minutes passed between the last_execution
        and utcnow()
        :param jql_statement:
        :param product_name:
        :return:
        """
        self.logger.info(
            f"'{product_name}' - submitting bug search request - {json.dumps({'jql_statement': jql_statement})}"
        )
        jql_statement_encoded = quote_plus(jql_statement)
        request_url = self.issues_endpoint_url.format(jql_statement_encoded)
        response = download_instance(link=request_url, headers=False, timeout=60)
        if not response:
            internal_error = f"{self.vendor_id}' - vendor API connection error | {request_url}"
            event_message = f"vendor API connection error - we are actively working on fix"
            self.logger.error(internal_error)
            raise ApiConnectionError(
                url=request_url, internal_message=internal_error,
                event_message=event_message
            )
        try:
            root = etree.fromstring(response.text)
        except (etree.ParserError, etree.XMLSyntaxError) as e:
            event_message = "vendor API response error - we are actively working on a fix"
            internal_message = f"'{self.vendor_id}' - API response error | check {jql_statement}"
            self.logger.error(internal_message)
            raise ApiResponseError(
                url=request_url, internal_message=internal_message,
                event_message=event_message
            ) from e

        for elem in root.getiterator():
            elem.tag = etree.QName(elem).localname
        etree.cleanup_namespaces(root)

        # The Parker convention absorbs the root element by default
        xml_client = Yahoo(xml_fromstring=False)
        try:
            bugs = xml_client.data(root)["rss"]["channel"]
            if "item" in bugs:
                bugs = bugs["item"]
            else:
                bugs = []
        except IndexError as e:
            self.logger.error(f"response rss schema is invalid - check {jql_statement}")
            event_message = "vendor API response error - we are actively working on a fix"
            internal_message = f"'{self.vendor_id}' - API rss response schema is invalid | check {jql_statement}"
            raise ApiResponseError(
                url=request_url, internal_message=internal_message,
                event_message=event_message
            ) from e
        except KeyError as e:
            self.logger.error(f"response rss schema is invalid - check {jql_statement}")
            event_message = "vendor API response error - we are actively working on a fix"
            internal_message = f"'{self.vendor_id}' - API rss response schema is invalid | check {jql_statement}"
            raise ApiResponseError(
                url=request_url, internal_message=internal_message,
                event_message=event_message
            ) from e

        self.logger.info(f"'{product_name}' - {len(bugs)} bugs retrieved")
        return bugs

    def format_bug_entry(self, bugs, managed_product_id, sn_ci_query_base):
        """
        convert MongoDB Jira bug entries
        :param bugs:
        :param managed_product_id:
        :param sn_ci_query_base:
        :return:
        """
        formatted_bugs = list()

        if isinstance(bugs, dict):
            bugs = [bugs]
        for bug in bugs:
            formatted_entry = dict()

            # mandatory fields
            # skipped bugs without affected versions
            if not bug.get("version", None):
                continue
            formatted_entry["knownAffectedReleases"] = ", ".join(bug.get("version", "")) \
                if isinstance(bug.get("version", ""), list) else bug.get("version", "")

            if not bug.get("key", None):
                continue
            formatted_entry["bugId"] = bug["key"]["id"]

            if not bug.get("priority", None):
                continue

            if not bug.get("priority").get("content", None):
                continue

            # convert sbPriority value to label
            priority = bug.get("priority").get("content", "")
            formatted_entry["priority"] = priority

            if not bug.get("status", None):
                continue

            if not bug.get("status").get("content", None):
                continue

            if sn_ci_query_base:
                sn_ci_query_base = f"{sn_ci_query_base}^"
            formatted_entry["status"] = bug.get("status", "").get("content", "")
            formatted_entry["bugUrl"] = bug.get("link", "")
            formatted_entry["summary"] = bug.get("title", "")
            formatted_entry["snCiFilter"] = f"{sn_ci_query_base}versionIN{','.join(bug['version'])}"
            formatted_entry["snCiTable"] = self.service_now_ci_table
            formatted_entry["vendorCreatedDate"] = self.timestamp_format(bug["created"][:-6])
            formatted_entry["vendorLastUpdatedDate"] = self.timestamp_format(bug["updated"][:-6])
            formatted_entry["managedProductId"] = managed_product_id
            formatted_entry["vendorId"] = self.vendor_id

            # format comments as full html - take the last 10 comments only
            comments_html = ""
            if "comments" in bug:
                comments = [bug["comments"]["comment"]] if isinstance(bug["comments"]["comment"], dict) \
                    else bug["comments"]["comment"]
                comments_html = "".join(
                    [f"<p>Author: {x['author']}</p><p>{x['created']}</p>{x.get('content', '')}" for x in comments[-10:]]
                )

            # concatenate comments_html to the bug description
            formatted_entry["description"] = bug.get("description", "") + comments_html
            formatted_entry["description"] = self.strip_html_spans(formatted_entry["description"])

            if isinstance(bug.get("fixVersion", ""), list):
                formatted_entry["knownFixedReleases"] = ", ".join(bug["fixVersion"])
            else:
                formatted_entry["knownFixedReleases"] = bug.get("fixVersion", "")

            os_values = []
            affected_os = []
            for x in bug.get("customfields", {"customfield": []})["customfield"]:
                if x['customfieldname'] == 'Operating System':
                    if 'customfieldvalues' in x and x['customfieldvalues']:
                        if isinstance(x['customfieldvalues'], dict):
                            x['customfieldvalues'] = [x['customfieldvalues']]

                        for item in x['customfieldvalues']:
                            os_values.append(item)

            for entry in os_values:
                if not entry.get("customfieldvalue", ""):
                    continue
                if entry["customfieldvalue"]["content"].lower() != "all":
                    affected_os.append(entry.get("content", ""))

            formatted_entry["knownAffectedOs"] = "".join(affected_os)

            formatted_entry["vendorData"] = {
                # converting datetime obj to string to store inside json # 2021-09-01 22:19:47
                "vendorResolvedDate": self.timestamp_format(bug.get("resolved", "")[:-6]).strftime("%Y-%m-%d %H:%M:%S"),
                "vendorResolution": bug.get('resolution', {"content": ""}).get("content", None),
                "views": bug.get("watches", None),
                "votes": bug.get("votes", None)
            }

            formatted_bugs.append(formatted_entry)

        return formatted_bugs

    @staticmethod
    def timestamp_format(time_str):
        """
        convert timedate objects to unified timedate string
        :param time_str:
        :return:
        """
        # max 6 digit micro second
        known_formats = [
            "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%a, %d %b %Y %H:%M:%S Z", "%a, %d %b %Y %H:%M:%SZ"
        ]
        fmt_time = ""
        for i, fmt in enumerate(known_formats):
            check_string = time_str
            if i != 2:
                check_string = time_str.strip("Z")[:25] + "Z"
            try:
                fmt_time = datetime.datetime.strptime(check_string, fmt)
                break
            except ValueError:
                continue
        if fmt_time:
            return fmt_time
        return time_str

    def prepare_managed_products(self, db_client, managed_products_table, last_executed_gap):
        """

        :param db_client:
        :param managed_products_table:
        :param last_executed_gap:
        :return:
        """
        recently_processed_products = db_client.conn.query(
            db_client.base.classes[managed_products_table].name,
            db_client.base.classes[managed_products_table].lastExecution,
            db_client.base.classes[managed_products_table].isDisabled,
        ).filter(
            or_(
                db_client.base.classes[managed_products_table].lastExecution > last_executed_gap,
                db_client.base.classes[managed_products_table].isDisabled == 1
            ),
            db_client.base.classes[managed_products_table].vendorId == self.vendor_id
        ).all()

        if [u.name for u in recently_processed_products]:
            processed_items = json.dumps(
                [
                    {'name': u.name, 'lastExecution': u.lastExecution, 'disabled': u.isDisabled}
                    for u in recently_processed_products
                ],
                default=str
            )
            logger.info(
                f"skipping disabled products and products processed in the last 6 hours - {processed_items}"
            )

        managed_products = db_client.conn.query(
            db_client.base.classes[managed_products_table]
        ).filter(
            or_(
                db_client.base.classes[managed_products_table].lastExecution <= last_executed_gap,
                db_client.base.classes[managed_products_table].lastExecution.is_(None)
            ),
            db_client.base.classes[managed_products_table].isDisabled != 1,
            db_client.base.classes[managed_products_table].vendorId == self.vendor_id
        ).all()

        if [u.name for u in managed_products]:
            items_to_process = json.dumps(
                [
                    {'name': u.name, 'lastExecution': u.lastExecution} for u in managed_products
                ], default=str)
            logger.info(
                f"to be processed managed products - {items_to_process}"
            )

            return managed_products
        return []

    def gen_search_filter_map(self, managed_product, minutes_since_last_execution):
        """
        generate the search filter map used to generate the JQL search bug statement, configuration is take from the
        managed product settings
        :param managed_product:
        :param minutes_since_last_execution:
        :return:
        """
        filter_map = {
            "project": {"operator": 'in', "value": managed_product.vendorData["vendorProjects"]},
            "issuetype": {"operator": "in", "value": ["Bug"]},
            "status": {"operator": "in", "value": managed_product.vendorStatuses},
            "affectedVersion": {"operator": "in", "value": managed_product.vendorData["productSoftwareVersions"]},
            "priority": {
                "operator": "in",
                "value": [x["vendorPriority"] for x in managed_product.vendorPriorities]
            },
            "resolution": {"operator": "in", "value": managed_product.vendorData["vendorResolutions"]},
            "resolved": {"operator": ">=", "value": f"-{minutes_since_last_execution}m"},
            "order": {"operator": "order", "value": "created", "direction": "ASC"},
        }
        self.logger.info(
            f"'{managed_product.name}' - search filter map generated | {json.dumps(filter_map, default=str)}"
        )
        return filter_map

    def sn_sync(self, sn_api_url, sn_auth_token, sn_ci_query_base):
        """
        keep managed products software version up to date with the correlating instances in the SN instance
        run sn queries to find product version in the SN instance
        :param sn_api_url:
        :param sn_auth_token:
        :param sn_ci_query_base:
        :return:
        """

        self.logger.info(f"'{self.vendor_id}' - initiating SN instances search")
        sn_query = f"{self.service_now_ci_table}?" \
                   f"sysparm_query={sn_ci_query_base}&" \
                   f"sysparm_fields=version"
        if sn_query in self.sn_query_cache:
            self.sn_query_cache[sn_query] += 1
            logger.info(
                f"'{self.vendor_id}' - skipping cached query url: {sn_query} | count: {self.sn_query_cache[sn_query]}")
            return False
        self.sn_query_cache[sn_query] = 1

        sn_query_url = f"{sn_api_url}/api/now/table/{sn_query}"
        response = download_instance(
            link=sn_query_url,
            headers={"Authorization": f"Basic {sn_auth_token}"}
        )
        if not response:
            self.logger.error(f"'{self.vendor_id}' - SN API connection error | {sn_query_url}")
            raise ApiConnectionError(
                url=sn_query_url, internal_message="SN API connection error",
                event_message="a connection to ServiceNow could not be established - check ServiceNow settings"
            )

        count = int(response.headers["x-total-count"])
        self.sn_query_cache[sn_query] += count
        if count:
            logger.info(f"'{self.vendor_id}' - {count} SN CI(s) found")
            try:
                instances = json.loads(response.text)["result"]
            except json.JSONDecodeError as e:
                raise ApiResponseError(
                    url=sn_query_url, internal_message="error parsing serviceNow response - check url",
                    event_message="ServiceNow query returned a malformed response - check ServiceNow settings"
                ) from e

            versions = set()

            if not instances:
                return False

            for item in instances:
                if item["version"]:
                    versions.add(item["version"])

            return sorted(list(versions))
        return False

    @staticmethod
    def strip_html_spans(html_string):
        """
        strip styling attributes out of <span> nodes
        :param html_string:
        :return:
        """
        html_string = re.sub('<span.*?>', "", html_string)
        html_string = re.sub('</span>', "", html_string)
        return html_string

    def sn_event_formatter(
            self, event_class, resource, node, metric_name, error_type, severity, description, additional_info="",
            source="bugzero",
    ):
        """
        generate an sn event dict record
        more info - https://bugzero.sharepoint.com/:w:/s/product/EV4azm0bPzVOhiuBIyMWQYcB49Rr2uZSHMcd8Edq5wDjlg?e=g7J1pF
        :param source: The Application stack(Serverless app name). Note: This should be static for all serverless
                       functions as they all inherit from our bugzero-serverless stack.
        :param event_class: Service name defined in serverless.yml
        :param resource: Function inside the service
        :param node: ServiceNow Application Service name (Match value inside name)
        :param metric_name: Error Message (System generated or specified)
        :param error_type: "Operational" or "Programmer"
        :param severity: {
                            "1": "The resource is either not functional or critical problems are imminent.",
                            "2": "Major functionality is severely impaired or performance has degraded.",
                            "3": "Partial, non-critical loss of functionality or performance degradation occurred.",
                            "4": "Attention is required, even though the resource is still functional.",
                            "5": "No severity. An alert is created. The resource is still functional."
                        }
        :param description: A stack trace of the error. This will help identify where the error occurred
        :param additional_info: optional - Any other additional information.
        :return:
        """
        event_record = {
            "source": source,
            "event_class": event_class,
            "resource": resource,
            "node": node,
            "metric_name": metric_name,
            "message_key": "",
            "type": error_type,
            "severity": severity,
            "description": description,
            "additional_info": additional_info
        }
        self.logger.info(f"generated SN event record - {json.dumps(event_record, default=str)}")
        return event_record
