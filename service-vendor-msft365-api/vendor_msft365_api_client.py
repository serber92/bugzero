#!/usr/bin/env python3
"""
created 2021-08-29
"""
import base64
import datetime
import json
import logging.config
import re
import sys

import boto3
import lxml.html
import requests
from botocore.exceptions import ClientError
from requests.packages import urllib3

from download_manager import download_instance
from vendor_exceptions import ApiResponseError, ApiConnectionError

urllib3.disable_warnings()
logger = logging.getLogger()


class Msft365ApiClient:
    """
    - a class with shared methods used msft 365 online services
    """
    def __init__(self, vendor_id="msft", bugs_days_back=2):
        """"""
        self.logger = logger
        # ------------------------------------------------------------------------------------------------------------ #
        #                                         GLOBAL VARIABLES                                                     #
        # ------------------------------------------------------------------------------------------------------------ #
        # counters
        self.bugs_days_back = 2
        self.bugs_inserted_counter = 0
        self.bugs_updated_counter = 0
        self.bugs_found_counter = 0
        self.db_execution_counter = 0
        self.processed_bugs = 0

        # data cache
        self.active_bugs_dedup = set()
        self.new_bugs = []
        self.sn_query_cache = {}
        self.sn_versions = {}

        self.earliest_bug_date = datetime.datetime.utcnow() - datetime.timedelta(days=bugs_days_back)
        self.utc_now = datetime.datetime.utcnow()
        self.now = datetime.datetime.now()
        self.earliest_execution = self.utc_now
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

    @staticmethod
    def timestamp_format(time_str):
        """
        convert timedate objects to unified timedate string
        :param time_str:
        :return:
        """
        # max 6 digit micro second
        known_formats = ["%Y-%m-%dT%H:%M:%SZ"]
        fmt_time = ""
        for _i, fmt in enumerate(known_formats):
            check_string = time_str.strip("Z")[:19] + "Z"
            try:
                fmt_time = datetime.datetime.strptime(check_string, fmt)
                break
            except ValueError:
                continue
        if fmt_time:
            return fmt_time
        return time_str

    def sn_sync(self, product_family, query_product, sn_api_url, sn_auth_token):
        """
        keep managed products software version up to date with the correlating instances in the SN instance
        run sn queries to find product version in the SN instance
        :param sn_api_url:
        :param sn_auth_token:
        :param product_family:
        :param query_product:
        :return:
        """
        sn_query = f"?sysparm_query={query_product.snCiFilter}&sysparm_fields=os_version,version"
        sn_query_url = f"{sn_api_url}/api/now/table/{query_product.snCiTable}{sn_query}"
        response = download_instance(
            link=sn_query_url,
            headers={"Authorization": f"Basic {sn_auth_token}"}, session=False
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
            logger.info(
                f"'{product_family.name}' '{query_product.name}' - {count} CI(s) found for product version"
            )
            return True
        return False

    def gen_admin_dashboard_tokens(self, username, password):
        """
        generate auth tokens for the msft admin dashboard
        :param username:
        :param password:
        :return:
        """
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/"
                      "apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "content-length": "",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://login.microsoftonline.com",
            "referer": "https://login.microsoftonline.com/",
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "cross-site",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/96.0.4664.110 Safari/537.36"
        }
        credentials_form = {
            "username": username,
            "isOtherIdpSupported": True,
            "checkPhones": False,
            "isRemoteNGCSupported": True,
            "isCookieBannerShown": False,
            "isFidoSupported": True,
            "originalRequest": "",
            "country": "US",
            "forceotclogin": False,
            "isExternalFederationDisallowed": False,
            "isRemoteConnectSupported": False,
            "federationFlags": 0,
            "isSignup": False,
            "flowToken": "",
            "isAccessPassSupported": True
        }
        login_form = {
            "i13": "0",
            "login": username,
            "loginfmt": username,
            "type": "11",
            "LoginOptions": "3",
            "lrt": "",
            "lrtPartition": "",
            "hisRegion": "",
            "hisScaleUnit": "",
            "passwd": password,
            "ps": "2",
            "psRNGCDefaultType": "",
            "psRNGCEntropy": "",
            "psRNGCSLK": "",
            "canary": "",
            "ctx": "",
            "hpgrequestid": "",
            "flowToken": "",
            "PPSX": "",
            "NewUser": "1",
            "FoundMSAs": "",
            "fspost": "0",
            "i21": "0",
            "CookieDisclosure": "0",
            "IsFidoSupported": "1",
            "isSignupPost": "0",
            "i2": "1",
            "i17": "",
            "i18": "",
            "i19": "81076"
        }
        kmsi_form = {
            "LoginOptions": "3",
            "type": "28",
            "ctx": "",
            "hpgrequestid": "",
            "flowToken": "",
            "canary": "",
            "i2": "",
            "i17": "",
            "i18": "",
            "i19": "1060492"
        }
        landing_form = {
            "code": "",
            "id_token": "",
            "state": "",
            "session_state": "",
            "correlation_id": ""
        }

        steps = [
            {
                "url": "https://admin.microsoft.com/login?ru=%2Fadminportal%2Fhome%3F", "parse_json": True,
                "parse_regex": True, "regex_string": r'(?<=\$Config=){".*?}(?=;)',
                "log_message": "creating login session", "error_message": "admin dashboard session creation failed",
                "post": False, "post_form": {},
                "store_fields": {"flowToken": "sFT", "canary": "canary", "ctx": "sCtx"},
                "json_form": False, "form_fields_map": {}, "form": False, "parse_html": False, 'xpaths': []
            },
            {
                "url": "https://login.microsoftonline.com/common/GetCredentialType?mkt=en-US", "parse_json": True,
                "parse_regex": False, "regex_string": r'',
                "log_message": "getting login credentials cookies",
                "error_message": "admin dashboard credentials cookie parse failed",
                "post": True, "post_form": {}, "form": credentials_form, "form_fields_map": ['flowToken'],
                "store_fields": {"flowToken": "FlowToken"}, 'xpaths': [],
                "json_form": True, "parse_html": False
            },
            {
                "url": "https://login.microsoftonline.com/common/login", "parse_json": True,
                "parse_regex": True, "regex_string": r'(?<=\$Config=){".*?}(?=;)',
                "log_message": "logging into admin dashboard", "error_message": "admin dashboard login failed",
                "post": True, "post_form": {}, "form": login_form, "form_fields_map": ['flowToken', 'canary', 'ctx'],
                "store_fields": {"canary": "canary", "flowToken": "sFT", "ctx": "sCtx"}, "json_form": False,
                "parse_html": False, 'xpaths': []
            },
            {
                "url": "https://login.microsoftonline.com/kmsi", "parse_json": False,
                "parse_regex": False, "regex_string": '',
                "log_message": "getting kmsi cookies", "error_message": "kmsi cookies retrieval failed",
                "post": True, "post_form": {}, "form": kmsi_form, "form_fields_map": ['canary', 'flowToken', 'ctx'],
                "store_fields": {}, "parse_html": True, "json_form": False,
                'xpaths': [
                    {"xpath": "//input[@name='code']/@value", "title": "code"},
                    {"xpath": "//input[@name='id_token']/@value", "title": "id_token"},
                    {"xpath": "//input[@name='state']/@value", "title": "state"},
                    {"xpath": "//input[@name='session_state']/@value", "title": "session_state"},
                    {"xpath": "//input[@name='correlation_id']/@value", "title": "correlation_id"}
                ],
            },
            {
                "url": "https://admin.microsoft.com/landing", "parse_json": False,
                "parse_regex": False, "regex_string": '',
                "log_message": "generating dashboard admin api tokens", "error_message": "token generation failed",
                "post": True, "post_form": {}, "form": landing_form,
                "form_fields_map": ['code', 'id_token', 'state', 'session_state', 'correlation_id'],
                "store_fields": {"canary": "canary", "flowToken": "sFT", "ctx": "sCtx"}, "json_form": False,
                "parse_html": False, 'xpaths': [], "headers": True
            },
        ]
        s = requests.session()
        stored_data = {}
        for i, step in enumerate(steps, 1):
            self.logger.info(f"'{self.vendor_id}' - admin dashboard auth step {i}/{len(steps)} | {step['log_message']}")
            if step["post"]:
                post_form = step['form']
                for field in step['form_fields_map']:
                    post_form[field] = stored_data[field]
                if step["json_form"]:
                    response = download_instance(link=step["url"], session=s, method="POST", json=post_form)
                else:
                    if step.get('headers'):
                        headers["content-length"] = str(len(json.dumps(post_form, default=str)))
                        response = download_instance(
                            link=step["url"], session=s, method="POST", payload=post_form, headers=headers)
                    else:
                        response = download_instance(link=step["url"], session=s, method="POST", payload=post_form)

            else:
                response = download_instance(link=step["url"], session=s)

            if not response:
                internal_message = f"'{self.vendor_id}' - {step['error_message']}"
                event_message = f"msft API error - can't log into the admin dashboard"
                raise ApiResponseError(
                    internal_message=internal_message, event_message=event_message, url=step["url"]
                )
            if step["parse_json"]:
                if step["parse_regex"]:
                    data_container = re.findall(step["regex_string"], response.text)
                    if not data_container:
                        internal_message = f"'{self.vendor_id}' - {step['error_message']}"
                        event_message = f"msft API error - can't log into the admin dashboard"
                        raise ApiResponseError(
                            internal_message=internal_message, event_message=event_message, url=step["url"]
                        )
                    data_container = data_container[0]
                else:
                    data_container = response.text
                try:
                    data = json.loads(data_container)
                except json.JSONDecodeError as e:
                    internal_message = f"'{self.vendor_id}' - {step['error_message']}"
                    event_message = f"msft API error - can't log into the admin dashboard"
                    raise ApiResponseError(
                        internal_message=internal_message, event_message=event_message, url=step["url"]
                    ) from e

                for k, v in step['store_fields'].items():
                    stored_data[k] = data[v]
                continue
            if step["parse_html"]:
                root = lxml.html.fromstring(response.text)
                for path in list(step["xpaths"]):
                    value = root.xpath(path["xpath"])
                    stored_data[path["title"]] = value

        cookies = s.cookies.get_dict()
        try:
            tokens = {
                "RootAuthToken": cookies['RootAuthToken'],
                'OIDCAuthCookie': cookies["OIDCAuthCookie"],
                'UserIndex': cookies['UserIndex']
            }
        except KeyError as e:
            internal_message = f"'{self.vendor_id}' - invalid credentials"
            event_message = f"msft API error - can't log into the admin dashboard"
            raise ApiResponseError(
                internal_message=internal_message, event_message=event_message,
                url="https://admin.microsoft.com/landing"
            ) from e

        return tokens

    def get_aws_secret_value(self, secret_name):
        """
        - retrieve secret value from AWS Secrets Manager
        :param secret_name:
        :return:
        """
        try:
            get_secret_value_response = self.secret_manager_client.get_secret_value(
                SecretId=secret_name
            )
            if "SecretString" in get_secret_value_response:
                secret = json.loads(get_secret_value_response["SecretString"])
                if not secret.get('username') or not secret.get('password'):
                    raise ValueError("AWS secret error - missing username and/or password", "SecretManager")
                return secret
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response["SecretBinary"]
            )
            return decoded_binary_secret
        except (ClientError, ValueError) as e:
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

    def filter_service_health_issues(self, managed_product, last_execution, service_issue):
        """
        filter service issues based on:
            1. issue type
            2. status
            3. bug date
        :param managed_product:
        :param last_execution:
        :param service_issue:
        :return:
        """
        self.logger.info(f"'{managed_product.name}' - filtering health issues")
        vendor_priorities = [x['vendorPriority'].lower() for x in managed_product.vendorPriorities]
        vendor_statuses = [x.lower() for x in managed_product.vendorStatuses]
        bugs = []

        for priority, v in service_issue.items():
            # filter by priority
            if priority.lower() not in vendor_priorities:
                continue
            for issue in v:
                issue_status = issue['MessageStatus'].get('DisplayName')
                # filter by status
                if issue_status.lower() not in vendor_statuses:
                    continue
                # filter by date
                issue_last_updated_object = self.timestamp_format(issue['LastUpdatedTime'])
                if last_execution > (issue_last_updated_object - datetime.timedelta(days=2)):
                    continue

                description = ""

                description_fields = [
                    {"title": "Service Feature", "field_name": 'FeatureDisplayName'},
                    {"title": "Impact", 'field_name': 'ImpactDescription'},
                    {"title": "User Impacted", "field_name": 'UserFunctionalImpact'},
                    {"title": 'Additional Diagnostics', "field_name": 'AdditionalDiagnostics'},
                    {"title": 'Recommendations', "field_name": 'recommendations'},
                    {"title": 'User Count Impact', "field_name": 'userCountImpact'},

                ]
                for f in description_fields:
                    if issue.get(f['field_name'], ""):
                        description += f"{f['title']}: {issue[f['field_name']]}\n"
                description += "\nAll Updates:\n"

                for message in issue["Messages"]:
                    timestamp = self.timestamp_format(
                        time_str=message['PublishedTime']
                    ).strftime("%B %d, %Y %H:%M %p")
                    service_message = f"------------------------------------------------------\n{timestamp}\n\n" \
                                      f"{message['MessageText']}\n"
                    description += service_message

                # issue passed all filters - format bug entry
                bug_entry = {
                    "bugId": issue["Id"],
                    "bugUrl": f"https://admin.microsoft.com/adminportal/home?#/servicehealth/history/:/alerts/"
                              f"{issue['Id']}",
                    "description": description,
                    "priority": priority.title(),
                    "snCiFilter": f"install_status=1^operational_status=1^osLIKE{managed_product.name}",
                    "snCiTable": "cmdb_ci_computer",
                    "summary": f"{issue['FeatureDisplayName'].title()} - {issue['Title']}",
                    "status": issue_status.title(),
                    "knownAffectedReleases": managed_product.name,
                    "vendorData": {
                        'userCountImpact': issue.get('userCountImpact', "")
                    },
                    "vendorCreatedDate": self.timestamp_format(issue['StartTime']),
                    "vendorLastUpdatedDate": self.timestamp_format(issue['LastUpdatedTime']),
                    "processed": 0,
                    "managedProductId": managed_product.id,
                    "vendorId": self.vendor_id,
                }
                bugs.append(bug_entry)
        return bugs

    def get_service_issues(self, days_back, tokens):
        """
        get issues and advisories for a given service
        :param days_back:
        :param tokens:
        :return:
        """
        headers = {
            "accept": "application/json",
            "cookie": f"RootAuthToken={tokens['RootAuthToken']}; "
                      f"UserIndex={tokens['UserIndex']}; "
                      f"OIDCAuthCookie={tokens['OIDCAuthCookie']}"
        }
        url = f"https://admin.microsoft.com/admin/api/servicehealth/status/activeCM?showResolved=true&numDays=" \
              f"{days_back}"
        self.logger.info(
            f"'{self.vendor_id}' - getting service issues | days back: {days_back}"
        )
        response = download_instance(link=url, headers=headers, session=False)
        if not response:
            internal_error = f"{self.vendor_id}' - vendor API connection error | {url}"
            event_message = f"vendor API connection error - we are actively working on fix"
            self.logger.error(internal_error)
            raise ApiConnectionError(
                url=url, internal_message=internal_error,
                event_message=event_message
            )
        try:
            services = json.loads(response.text)
            if not services['ServiceStatus']:
                internal_error = f"'{self.vendor_id}' - vendor API response empty error | {url}"
                event_message = f"vendor API response error - we are actively working on fix"
                self.logger.error(internal_error)
                raise ApiResponseError(
                    url=url, internal_message=internal_error,
                    event_message=event_message
                )
            return services['ServiceStatus']
        except json.JSONDecodeError as e:
            internal_message = f"'{self.vendor_id}' - API response error | failed to generate auth tokens"
            event_message = f"{self.vendor_id} - API connection error, we are actively working on a fix"
            self.logger.error(internal_message)
            raise ApiResponseError(
                url=url, internal_message=internal_message, event_message=event_message
            ) from e
