"""
created 2021-04-27
"""

import base64
import datetime
import json
import logging.config
import queue
import sys
import threading

import boto3
from botocore.exceptions import ClientError
from requests.packages import urllib3

from download_manager import download_instance
from vendor_exceptions import ApiConnectionError, ApiResponseError

urllib3.disable_warnings()
logger = logging.getLogger()


class CiscoApiClient:
    """
    - a class with methods to consume CiscoAPI, work with Aurora Serverless MySQL tables
    - errors are logged and reported as service now events
    """

    def __init__(
            self,
            vendor_id,
            service_now_ci_table="cmdb_ci",
    ):
        """"""
        # ------------------------------------------------------------------------------------------------------------ #
        #                                                   GLOBAL VARIABLES                                           #
        # ------------------------------------------------------------------------------------------------------------ #
        self.bug_ids = set()
        self.dedup_count = 0
        self.bugs = dict()
        self.logger = logger
        self.secret_manager_client = boto3.Session().client("secretsmanager")
        self.service_now_ci_table = service_now_ci_table
        self.vendor_id = vendor_id
        self.thread_error_tracker = 0

    def bugs_by_prod_family_and_sv(
            self,
            cisco_service_token,
            product_family_name,
            products,
    ):
        """
        retrieve all bugs for a given cisco product family name and affected software versions
        documentation: https://developer.cisco.com/docs/support-apis/#!bug/search-bugs-by-product-name-and-affected-
                       software-release
        :param cisco_service_token: oauth token info
        :param product_family_name: family name
        :param products: a list of grouped products by prod family
        :return:
        """
        self.bugs = {}
        headers = {
            "Authorization": f"{cisco_service_token['token_type']} {cisco_service_token['access_token']}",
            "Accept": "application/json",
        }

        # collect all the software versions,
        software_versions = list({prod.get("swVersion") for prod in products if prod.get("swVersion")})

        # max 50 unique versions in each query
        software_versions = [
            software_versions[i: i + 50] for i in range(0, len(software_versions), 50)
        ]

        # earliest bug date datetime obj
        pagination_urls = list()

        # generate a request for each group of software versions, getting all severities
        for group in software_versions:
            group_str = ",".join(group)
            api_url = (
                f"https://api.cisco.com/bug/v3.0/bugs/product_series/{product_family_name}/affected_releases/"
                f"{group_str}?modified_date=5&page_index=1"
            )
            self.logger.info(f"'{product_family_name}' - getting bug updates | {api_url}")
            request = download_instance(link=api_url, headers=headers)
            if not request:
                internal_message = f"'{product_family_name}' - API connection error | {api_url}"
                event_message = f"{self.vendor_id} - API connection error, we are actively working on a fix"
                self.logger.error(internal_message)
                raise ApiConnectionError(
                    url=api_url, internal_message=internal_message, event_message=event_message
                )

            results = json.loads(request.text)
            if not results["pagination_response_record"].get("total_records"):
                continue

            # iterate bugs
            for bug in results["bugs"]:
                if bug["bug_id"] in self.bug_ids:
                    self.dedup_count += 1
                    continue

                self.bug_ids.add(bug["bug_id"])

                bug["priority"] = bug['severity']
                self.bugs[bug["bug_id"]] = bug

            # if the response is paginated - append url to pagination_urls
            if results["pagination_response_record"]["last_index"] > 1:
                for page in range(
                        2, results["pagination_response_record"]["last_index"] + 1
                ):
                    api_url = (
                        f"https://api.cisco.com/bug/v3.0/bugs/product_series/{product_family_name}"
                        f"/affected_releases/{group_str}?modified_date=5&page_index={page}"
                    )
                    pagination_urls.append(api_url)

        # process existing pagination_urls in the multi-threaded manager
        if pagination_urls:
            q = queue.Queue()
            for i, _url in enumerate(pagination_urls):
                q.put((i, pagination_urls[i], product_family_name))

            # 7 threads has been tested to be ideal
            num_threads = 7
            for i in range(num_threads):
                t = threading.Thread(
                    target=self.multi_threaded_manager, args=(q, headers)
                )
                t.start()

            q.join()

        if self.thread_error_tracker:
            internal_message = f"'{product_family_name}' - API connection error | {pagination_urls[0]}"
            event_message = f"{self.vendor_id} - API connection error, we are actively working on a fix"
            self.logger.error(internal_message)
            raise ApiConnectionError(
                url=pagination_urls[0], internal_message=internal_message, event_message=event_message
            )
        return self.bugs

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

    def filter_bugs(
            self, bugs, earliest_bug_date, vendor_statuses, vendor_severities, products, managed_product_id,
            sn_ci_query_base
    ):
        """
         1. filter bugs older than the lastExecution date -2 days
         2. filter bugs based on status
         3. filter bugs based on priority
        :param bugs:
        :param earliest_bug_date:
        :param vendor_statuses: F/O/T (FIXED/OPEN/TERMINATED)
        :param vendor_severities: bug severity level 1-5
        :param managed_product_id:
        :param products:
        :param sn_ci_query_base:
        :return:
        """
        if sn_ci_query_base:
            sn_ci_query_base = f"^{sn_ci_query_base}"
        filtered_bugs = list()
        for _bug_id, bug_data in bugs.items():
            bug_data["last_modified_date"] = datetime.datetime.strptime(
                bug_data["last_modified_date"][:10], "%Y-%m-%d"
            )
            # 1. filter bugs older than the lastExecution date -2 days
            if earliest_bug_date:
                if (bug_data["last_modified_date"] + datetime.timedelta(days=2)) <= earliest_bug_date:
                    continue

            # 2. filter bugs based on status
            if bug_data.get("status", "") not in vendor_statuses:
                continue

            # 3. filter bugs based on priority
            if bug_data.get("priority", "") not in vendor_severities:
                continue

            # convert convert label to value
            bug_data["priority"] = vendor_severities[bug_data["priority"]]

            bug_data["description"] = bug_data["description"].strip()
            bug_data["managedProductId"] = managed_product_id
            bug_data["knownAffectedReleases"] = ", ".join(bug_data.get("known_affected_releases", []).split(" "))
            bug_data["knownFixedReleases"] = ", ".join(bug_data.get("known_fixed_releases", [""]).split(" "))
            bug_data["bugId"] = bug_data["bug_id"]
            bug_data["bugUrl"] = f"https://bst.cloudapps.cisco.com/bugsearch/bug/{bug_data['bugId']}"
            bug_data["vendorLastUpdatedDate"] = bug_data["last_modified_date"]
            bug_data["summary"] = bug_data.get("headline", "")
            bug_data["processed"] = 0

            bug_data["vendorId"] = self.vendor_id
            bug_data["status"] = vendor_statuses[bug_data["status"]]
            bug_data["snCiTable"] = self.service_now_ci_table
            products_serial_numbers = ",".join(
                [x["serialNumber"] for x in products if x["serialNumber"]]
            )

            if products_serial_numbers:
                bug_data["snCiFilter"] = f"serial_numberIN{products_serial_numbers}{sn_ci_query_base}"
            else:
                # cant find serial numbers for inventory products ( can't attach to an SN CI )
                bug_data["snCiFilter"] = ""

            bug_data["vendorData"] = {
                "supportCasesCount": bug_data.get("support_case_count", ""),
                "knownAffectedVersions": bug_data.get("known_affected_releases", "").split(","),
                "behaviorChanged": bug_data.get("behavior_changed", ""),
            }

            # remove unnecessary fields
            remove_fields = [
                "bug_id",
                "last_modified_date",
                "headline",
                "severity",
                "known_affected_releases",
                "known_fixed_releases",
                "support_case_count",
                "product_series",
                "behavior_changed",
                "products",
                "id",
            ]

            for f in remove_fields:
                bug_data.pop(f, None)
            filtered_bugs.append(bug_data)
        return filtered_bugs

    def generate_service_api_token(self, cisco_client_id, cisco_client_secret):
        """
        - generate tokens for Cisco service API
        - ttl is 3600 sec by default
        :param cisco_client_id:
        :param cisco_client_secret:
        :return:
        """

        api_url = (
            f"https://cloudsso.cisco.com/as/token.oauth2?grant_type=client_credentials&"
            f"client_id={cisco_client_id}&client_secret={cisco_client_secret}"
        )
        request = download_instance(link=api_url, method="POST", headers=False)
        if not request:
            internal_message = f"'{self.vendor_id}' - API connection error | failed to generate auth tokens"
            event_message = f"{self.vendor_id} - API connection error, we are actively working on a fix"
            self.logger.error(internal_message)
            raise ApiConnectionError(
                url=api_url, internal_message=internal_message, event_message=event_message
            )
        try:
            service_api_auth = json.loads(request.text)
        except json.JSONDecodeError as e:
            internal_message = f"'{self.vendor_id}' - API response error | failed to generate auth tokens"
            event_message = f"{self.vendor_id} - API connection error, we are actively working on a fix"
            self.logger.error(internal_message)
            raise ApiResponseError(
                url=api_url, internal_message=internal_message, event_message=event_message
            ) from e

        if service_api_auth.get("error", None):
            if service_api_auth.get("error") == "invalid_client":
                internal_message = f"'{self.vendor_id}' - API connection error | bad credentials"
                event_message = f"{self.vendor_id} - API connection error | check your {self.vendor_id} credentials"
                self.logger.error(internal_message)
                raise ApiConnectionError(
                    url=api_url, internal_message=internal_message, event_message=event_message
                )

            internal_message = f"'{self.vendor_id}' - API connection error | authentication failed"
            event_message = f"{self.vendor_id} - API connection error | check your {self.vendor_id} credentials"
            raise ApiConnectionError(
                url=api_url, internal_message=internal_message, event_message=event_message
            )
        return service_api_auth

    def generate_support_api_tokens(self, cisco_client_id, cisco_client_secret):
        """
        - generate tokens for Cisco Support API
        - ttl is 3600 sec by default
        :param cisco_client_id:
        :param cisco_client_secret:
        :return:
        """

        api_url = (
            f"https://cloudsso.cisco.com/as/token.oauth2?grant_type=client_credentials&"
            f"client_id={cisco_client_id}&client_secret={cisco_client_secret}"
        )
        request = download_instance(link=api_url, method='POST', headers=False)
        if not request:
            internal_message = f"'{self.vendor_id}' - API connection error | failed to generate auth tokens"
            event_message = f"{self.vendor_id} - API connection error, we are actively working on a fix"
            self.logger.error(internal_message)
            raise ApiConnectionError(
                url=api_url, internal_message=internal_message, event_message=event_message
            )

        try:
            support_api_auth = json.loads(request.text)
        except json.JSONDecodeError as e:
            internal_message = f"'{self.vendor_id}' - API response error | failed to generate auth tokens"
            event_message = f"{self.vendor_id} - API connection error, we are actively working on a fix"
            self.logger.error(internal_message)
            raise ApiResponseError(
                url=api_url, internal_message=internal_message, event_message=event_message
            ) from e
        if support_api_auth.get("error", None):
            if support_api_auth.get("error") == "invalid_client":
                internal_message = f"'{self.vendor_id}' - API connection error | bad credentials"
                event_message = f"{self.vendor_id} - API connection error | check your {self.vendor_id} credentials"
                self.logger.error(internal_message)
                raise ApiConnectionError(
                    url=api_url, internal_message=internal_message, event_message=event_message
                )
            internal_message = f"'{self.vendor_id}' - API connection error | authentication failed"
            event_message = f"{self.vendor_id} - API connection error | check your {self.vendor_id} credentials"
            raise ApiConnectionError(
                url=api_url, internal_message=internal_message, event_message=event_message
            )
        return support_api_auth

    def get_hardware_inventory(self, cisco_customer_id, cisco_service_token):
        """
        - get complete inventory data from Cisco Service API for a given client
        - documentation: https://developer.cisco.com/docs/service-apis/#!inventory/inventory
        :param cisco_customer_id: customer ID for service API
        :param cisco_service_token: oauth token for service API
        :return:
        """
        headers = {
            "Authorization": f"{cisco_service_token['token_type']} {cisco_service_token['access_token']}",
            "Accept": "application/json",
        }
        api_url = f"https://apx.cisco.com/cs/api/v1/inventory/hardware?customerId={cisco_customer_id}"
        request = download_instance(link=api_url, headers=headers)
        if not request:
            internal_message = f"'{self.vendor_id}' - API connection error  | failed to get products inventory | " \
                               f"{api_url}"
            event_message = f"{self.vendor_id} - API connection error, we are actively working on a fic"
            self.logger.error(internal_message)
            raise ApiConnectionError(event_message=event_message, internal_message=internal_message, url=api_url)
        try:
            hardware_inventory = json.loads(request.text)["data"]
        except json.JSONDecodeError as e:
            internal_message = f"'{self.vendor_id}' - API response error  | failed to get products inventory | " \
                               f"{api_url}"
            event_message = f"{self.vendor_id} - API connection error, we are actively working on a fix"
            self.logger.error(internal_message)
            raise ApiResponseError(
                url=api_url, internal_message=internal_message, event_message=event_message
            ) from e
        return hardware_inventory

    def get_service_api_customer_id(self, cisco_service_token):
        """
        get customer_id from the Cisco Service API customer-info endpoint
        :param cisco_service_token:
        :return:
        """
        headers = {
            "Authorization": f"{cisco_service_token['token_type']} {cisco_service_token['access_token']}",
            "Accept": "application/json",
        }
        api_url = "https://apx.cisco.com/cs/api/v1/customer-info/customer-details"
        request = download_instance(link=api_url, headers=headers)
        if not request:
            internal_message = f"'{self.vendor_id}' - API connection error | failed to get customer info | {api_url}"
            event_message = f"{self.vendor_id} - API connection error, we are actively working on a fix"
            self.logger.error(internal_message)
            raise ApiConnectionError(
                url=api_url, internal_message=internal_message, event_message=event_message
            )
        try:
            return json.loads(request.text)["data"][0]
        except json.JSONDecodeError as e:
            internal_message = f"'{self.vendor_id}' - API response error | failed to get customer info | {api_url}"
            event_message = f"{self.vendor_id} - API response error, we are actively working on a fix"
            self.logger.error(internal_message)
            raise ApiConnectionError(
                url=api_url, internal_message=internal_message, event_message=event_message
            ) from e

    def multi_threaded_manager(self, q, headers):
        """
        multi-threaded download manager
        :return:
        """

        def api_request(entry):
            self.logger.info(f"'{entry[-1]}' - getting bug updates | {entry[1]}")
            response = download_instance(link=entry[1], headers=headers)
            if response:
                results = json.loads(response.text)
                if not results["pagination_response_record"]["total_records"]:
                    return
                for bug in results["bugs"]:
                    if bug["bug_id"] in self.bug_ids:
                        self.dedup_count += 1
                        self.bug_ids.add(bug["bug_id"])

                    bug["priority"] = bug['severity']
                    self.bugs[bug["bug_id"]] = bug
            else:
                self.thread_error_tracker += 1
                error = {
                    "url": {entry[1]},
                    "errorType": "connection error",
                    "errorMsg": "download failed with max retires",
                    "source": "Cisco Support - Bug API V3.0",
                    "service": f"vendor_cisco_api_client.py - line 560",
                }
                self.logger.error(f"download error - {json.dumps(error, default=str)}")

        while not q.empty():
            queue_object = q.get()
            api_request(entry=queue_object)
            q.task_done()

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

    def cisco_authentication(self, cisco_config):
        """
        get secrets from AWS SecretManager
        generate Cisco authentication tokens and retrieve client id
        :param cisco_config:
        :return:
        """
        cisco_service_cred = self.get_aws_secret_value(
            secret_name=cisco_config["serviceSecretId"]
        )

        # generate cisco service API oath auth ( for hardware inventory )
        service_token = self.generate_service_api_token(
            cisco_client_id=cisco_service_cred["ClientId"],
            cisco_client_secret=cisco_service_cred["ClientSecret"],
        )

        cisco_support_cred = self.get_aws_secret_value(
            secret_name=cisco_config["supportSecretId"],
        )

        # generate cisco support API oath auth ( for bug API v3.0 )
        support_token = self.generate_support_api_tokens(
            cisco_client_id=cisco_support_cred["ClientId"],
            cisco_client_secret=cisco_support_cred["ClientSecret"],
        )

        # get the cisco call home customerId
        cisco_customer_id = self.get_service_api_customer_id(
            cisco_service_token=service_token
        )

        logger.info(f"'{self.vendor_id}' - authentication flow completed | {cisco_customer_id}")
        return cisco_customer_id, support_token, service_token

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
