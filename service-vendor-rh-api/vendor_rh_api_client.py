#!/usr/bin/env python3
"""
created 2021-10-07
"""
import base64
import datetime
import importlib
import inspect
import json
import logging.config
import math
import os
import sys
import threading
from queue import Queue

import boto3
import lxml.html
import pytest
from botocore.exceptions import ClientError
from lxml import etree
from requests.packages import urllib3
from vendor_rh_exceptions import ApiResponseError, ApiConnectionError

from download_manager import download_instance

urllib3.disable_warnings()
logger = logging.getLogger()

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
common_service = importlib.import_module("service-common.python.lib.sn_utils")


class RedHatApiClient:
    """
    - a class with methods to consume https://bugzilla.redhat.com/, work with Aurora Serverless MySQL tables
    - errors are logged and reported as service now events
    """
    @pytest.mark.skip(reason="class initializer - nothing to test")
    def __init__(
            self,
            vendor_id,
    ):  # pragma: no cover
        """"""
        # ------------------------------------------------------------------------------------------------------------ #
        #                                                   GLOBAL VARIABLES                                           #
        # ------------------------------------------------------------------------------------------------------------ #
        self.bug_ids = set()
        self.dedup_count = 0
        self.bugs = []
        self.logger = logger
        self.sn_versions = []
        self.vendor_id = vendor_id
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

    @pytest.mark.skip(reason="function is not currently used - will be tested in future versions")
    def get_vendor_products(self, supported_classifications):  # pragma: no cover
        """
        consume the jsonPRC endpoint and retrieved a list of products filtered by the supported_classifications
        :param supported_classifications:
        :return:
        """
        headers = {
            "content-length": 0,
            "content-type": "application/json"
        }
        payload = {
            "jsonrpc": "2.0", "method": "SelectizeJS.list_products", "id": 1,
            "params": [{"term": "..", "disabled": 1, "classification": supported_classifications}]
        }
        headers["content-length"] = str(len(json.dumps(payload)))

        base_url = "https://bugzilla.redhat.com/jsonrpc.cgi"
        self.logger.info(f"getting vendor products - {payload}")
        response = download_instance(link=base_url, method="POST", headers=headers, json=payload)
        return json.loads(response.text)

    def get_bugs(self, search_url, product_name, offset_increments=20):
        """
        consume bugzilla.redhat.com with product specific generated search_url
        and utcnow()
        :param search_url:
        :param offset_increments:
        :param product_name:
        :return:
        """
        bugs = []
        self.logger.info(f"'{product_name}' - submitting bug search request | {search_url}")
        # store offset
        offset = 0
        total_matches = 1
        page_count = 1
        while total_matches > offset:
            url_w_offset = search_url + f"&limit={offset_increments}&offset={offset}"
            response = download_instance(link=url_w_offset, headers=False, timeout=60)
            if not response:
                raise ApiConnectionError(
                    url=search_url, internal_message="vendor API connection error - check url",
                    event_message="connection to vendor api failed"
                )
            try:
                results = json.loads(response.text)
                bugs.extend(results["bugs"])
                total_matches = results["total_matches"]
                total_pages = math.ceil(int(total_matches) / 20)
                offset += offset_increments
                self.logger.info(f"'{product_name}' - page {page_count}/{total_pages} retrieved | "
                                 f"bugs {len(bugs)}/{total_matches} retrieved")
                page_count += 1

            except (json.JSONDecodeError, IndexError) as e:
                self.logger.error(f"response parse failed - check {search_url}")
                raise ApiResponseError(
                    url=search_url, internal_message="error parsing response - check url",
                    event_message="connection to vendor api failed"
                ) from e
        return bugs

    def format_bug_entry(self, bugs, managed_product, sn_ci_filter, sn_ci_query_base, service_now_ci_table):
        """
        format product bugs to bz bug entries
        :param bugs:
        :param managed_product:
        :param sn_ci_filter:
        :param service_now_ci_table:
        :param sn_ci_query_base:
        :return:
        """
        formatted_bugs = list()
        if sn_ci_query_base:
            sn_ci_query_base = f"^{sn_ci_filter}"

        if isinstance(bugs, dict):
            bugs = [bugs]
        for bug in bugs:
            formatted_entry = dict()

            # mandatory fields
            # skipped bugs without affected versions
            if not bug.get("version", None):
                continue

            if isinstance(bug.get("version", ""), list):
                known_affected_releases = [f"{managed_product.name} v{x}" for x in bug.get("version")]
            elif bug.get("version", ""):
                known_affected_releases = [f"{managed_product.name} {bug.get('version')}"]
            else:
                known_affected_releases = []
            formatted_entry["knownAffectedReleases"] = ", ".join(known_affected_releases)

            if isinstance(bug.get("cf_fixed_in", None), list):
                known_fixed_releases = list(bug.get("cf_fixed_in"))
            elif bug.get("cf_fixed_in", ""):
                known_fixed_releases = [bug.get('cf_fixed_in')]
            else:
                known_fixed_releases = []

            formatted_entry["knownFixedReleases"] = ", ".join(known_fixed_releases)

            missing_mandatory_field = False
            mandatory_fields = ["id", "priority", "status"]
            for field in mandatory_fields:
                if not bug.get(field, None):
                    self.logger.error(f"'{managed_product.name}' - bug missing mandatory field '{field}' - "
                                      f"{json.dumps(bug, default=str)}")
                    missing_mandatory_field = True
                    break
            if missing_mandatory_field:
                continue

            formatted_entry["bugId"] = str(bug["id"])
            formatted_entry["description"] = bug["description"]
            formatted_entry["priority"] = bug.get("priority").title()
            formatted_entry["status"] = bug.get("status").title()
            formatted_entry["bugUrl"] = f"https://bugzilla.redhat.com/show_bug.cgi?id={bug['id']}"
            formatted_entry["summary"] = bug.get('summary', "")
            formatted_entry["knownAffectedOs"] = bug.get('op_sys', None)
            formatted_entry["snCiFilter"] = f"{sn_ci_filter}{sn_ci_query_base}"
            formatted_entry["snCiTable"] = service_now_ci_table
            formatted_entry["vendorCreatedDate"] = self.timestamp_format(bug["creation_time"])
            formatted_entry["vendorLastUpdatedDate"] = self.timestamp_format(bug["last_change_time"])
            formatted_entry["managedProductId"] = managed_product.id
            formatted_entry["vendorId"] = self.vendor_id
            formatted_entry["vendorData"] = {
                "votes": bug.get("votes", ""),
                "commentsCount": bug.get('longdescs.count', ""),
                "vendorProductName": managed_product.name,
                "vendorResolution": bug.get("resolution", "").title() if bug.get("resolution", "") else ""
            }

            formatted_bugs.append(formatted_entry)

        return formatted_bugs

    def get_bug_description_from_html(self, q):  # pragma: no cover => function not used
        """

        :param q:
        :return:
        """
        def download_description(bug):
            """
            download HTML and parse out the first comment as the description field
            :param bug:
            :return:
            """
            self.logger.info(
                f"'{bug['vendorData']['vendorProductName']}' - bug '{bug['bugUrl']}' description retrieved"
            )
            response = download_instance(link=bug['bugUrl'], headers=False)
            if not response:
                self.logger.error(f"'{bug['vendorData']['vendorProductName']}' - bug '{bug['bugId']}' download failed")
                return

            root = lxml.html.fromstring(response.text)
            description_container = root.xpath('//div[@id="c0"]/*[@class="bz_comment_text"]')
            first_comment_container = root.xpath('//div[@id="c1"]/*[@class="bz_comment_text"]')

            if not description_container and not first_comment_container:
                self.logger.error(
                    f"'{bug['vendorData']['vendorProductName']}' - bug '{bug['bugUrl']}' description parse error"
                )
                description = f"For more details please visit: {bug['bugUrl']}"
            elif description_container:
                description = etree.tostring(description_container[0], pretty_print=True).decode("utf-8")
            else:
                description = etree.tostring(first_comment_container[0], pretty_print=True).decode("utf-8")
            bug["description"] = description

        while not q.empty():
            queue = q.get()
            download_description(bug=queue)
            q.task_done()

    @pytest.mark.skip(reason="nothing to test here")
    def bug_description_multi_processing(self, bugs, num_threads=30):  # pragma: no cover
        """
        multi-processing manager to retrieve bugs_description
        :param bugs:
        :param num_threads:
        :return:
        """
        # self.bugs = []
        q = Queue()

        for bug in bugs:
            q.put(bug)

        for _ in range(num_threads):
            t = threading.Thread(target=self.get_bug_description_from_html, args=(q,))
            t.start()

        q.join()
        return bugs

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

    def sn_sync(self, query_product, sn_api_url, sn_auth_token, sn_ci_query_base, version_field="os_version"):
        """
        keep managed products software version up to date with the correlating instances in the SN instance
        run sn queries to find product version in the SN instance
        :param sn_api_url:
        :param sn_auth_token:
        :param version_field:
        :param query_product:
        :param sn_ci_query_base:
        :return:
        """
        if sn_ci_query_base:
            sn_ci_query_base = f"^{sn_ci_query_base}"
        sn_query = f"?sysparm_fields={query_product['sysparm_fields']}&sysparm_query={query_product['sysparm_query']}" \
                   f"{sn_ci_query_base}"
        query_product["sn_ci_versions"] = []
        sn_query_url = f"{sn_api_url}/api/now/table/{query_product['service_now_ci_table']}{sn_query}"
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
                f"'{query_product['value']}' - {count} SN CI(s) found")
            try:
                instances = json.loads(response.text)["result"]
            except json.JSONDecodeError as e:
                raise ApiResponseError(
                    url=sn_query_url, internal_message="error parsing serviceNow response - check url",
                    event_message="ServiceNow query returned a malformed response - check ServiceNow settings"
                ) from e
            versions = set()

            for item in instances:
                if item[version_field]:
                    versions.add(item[version_field])

            query_product["sn_ci_versions"] = list(versions)
        else:
            self.logger.info(
                f"'{query_product['value']}' - No SN CIs found")
        return query_product

    def generate_api_search_url(
            self, name, vendor_priorities, vendor_statuses, vendor_resolutions, versions, start_date, end_date
    ):
        """

        :param name:
        :param vendor_priorities:
        :param vendor_statuses:
        :param vendor_resolutions:
        :param versions:
        :param start_date:
        :param end_date:
        :return:
        """
        # cf_fixed_in - fixed in version, longdescs.count = comments count
        url = f"https://bugzilla.redhat.com/rest/bug?product={name}" \
              f"&chfieldfrom={start_date}" \
              f"&chfieldto={end_date}" \
              "&include_fields=product,id,description,summary,version,status,priority,last_change_time,creation_time," \
              "op_sys,votes,cf_fixed_in,longdescs.count,resolution"

        statuses_query_string = "".join([f"&bug_status={s}" for s in vendor_statuses])
        priorities_query_string = "".join([f"&priority={p['vendorPriority']}" for p in vendor_priorities])
        versions_query_string = "".join([f"&version={v}" for v in versions])
        resolution_query_string = "".join([f"&resolution={r}" for r in vendor_resolutions])
        # include empty resolution query string for open bugs
        empty_resolution_query_string = "&resolution=---"
        url += statuses_query_string + priorities_query_string + versions_query_string + resolution_query_string + \
            empty_resolution_query_string
        search_parameters = {
            "product": name,
            "vendorStatuses": vendor_statuses,
            "vendorPriorities":  [p['vendorPriority'] for p in vendor_priorities],
            "vendorResolution": vendor_resolutions,
            "versions": versions,
            "startDate": start_date,
            "endDate": end_date,
        }

        #
        self.logger.info(f"'{name}' - generated search url filters | {json.dumps(search_parameters, default=str)}")
        return url
