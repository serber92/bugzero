#!/usr/bin/env python3
"""
created 2021-11-06
"""
import base64
import datetime
import importlib
import inspect
import json
import logging.config
import os
import random
import re
import sys

import boto3
import lxml.html
import pytest
import requests
from botocore.exceptions import ClientError
from requests.packages import urllib3

from download_manager import download_instance
from vendor_exceptions import ApiResponseError, ApiConnectionError, ApiAuthenticationError

urllib3.disable_warnings()
logger = logging.getLogger()

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
common_service = importlib.import_module("service-common.python.lib.sn_utils")


class NetAppApiClient:
    """
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
        self.oam_session = requests.session()
        self.secret_manager_client = boto3.Session().client("secretsmanager")
        self.sn_table = "cmdb_ci_storage_server"
        self.account_systems = {}

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

    @staticmethod
    def timestamp_format(time_str):
        """
        convert timedate strings to timedate objects
        :param time_str:
        :return:
        """
        # max 6 digit micro second
        if time_str:
            time_str = time_str[:19]
            known_formats = [
                "%Y-%m-%dT%H:%M:%S", "%B %d, %Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ",
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
        return None

    def generate_api_tokens_v2(self, refresh_token):
        """
        use a refresh token to generate an access token and a new refresh token
        :param refresh_token:
        :return:
        """
        api_url = 'https://api.activeiq.netapp.com/v1/tokens/accessToken'
        session = requests.session()
        token_request_form = {
            "refresh_token": refresh_token
        }
        response = download_instance(
            session=session, link=api_url, method="POST", json=token_request_form, data={}, headers=None
        )
        if not response:
            message = f"'{self.vendor_id}' connection error | terminating service"
            event_message = 'vendor authentication error - please verify the API token in the vendor ' \
                            'configuration page'
            self.logger.error(message)
            raise ApiAuthenticationError(url=api_url, internal_message=message, event_message=event_message)

        try:
            data = json.loads(response.text)
            if not data:
                message = f"'{self.vendor_id}' generating API tokens - empty response | terminating service"
                event_message = 'vendor authentication error - ' \
                                ' please verify the API token in the vendor configuration page'
                self.logger.error(message)
                raise ApiAuthenticationError(url=api_url, internal_message=message, event_message=event_message)

            refresh_token_masked = f"........................{data['refresh_token'][-50:]}"
            self.logger.info(f"'{self.vendor_id}' - API tokens retrieved successfully  - {refresh_token_masked}")
            return data
        except json.JSONDecodeError as e:
            message = f"'{self.vendor_id}' generating API tokens - response parse error | terminating service"
            event_message = 'vendor authentication error - please verify the API token in the vendor ' \
                            'configuration page'
            self.logger.error(message)
            raise ApiResponseError(url=api_url, event_message=event_message, internal_message=message) from e

    def generate_api_tokens(self, netapp_user, netapp_password):
        """
        1. create a login session
        2. login to netApp ActiveIQ
        3. generate API access tokens
        :return:
        """
        login_steps = [
            {"url": "https://activeiq.netapp.com/", "name": "creating MySupport session", "method": "GET",
             "form": None},
            {"url": "https://login.netapp.com/oam/server/auth_cred_submit/", "name": "logging in", "method": "POST",
             "form": f"action=login&username={netapp_user}&password={netapp_password}"},
            {"url": "https://activeiq.netapp.com/api", "name": "activating active QI", "method": "GET", "form": None},
            {"url": "https://login.netapp.com/ms_oauth/oauth2/endpoints/oauthservice/authorize?response_type=code&"
                    "scope=AsupUserProfile.me&client_id=MyAsupAPI&redirect_uri=https%3A%2F%2Factiveiq.netapp.com%2Fapi",
             "name": "authorizing API user", "method": "GET", "form": None}
        ]
        gen_token_url = "https://api.activeiq.netapp.com/v1/tokens/token"

        session = requests.session()
        token_request_form = {
            "code": "", "redirect_uri": "https://activeiq.netapp.com/api"
        }
        for i, step in enumerate(login_steps, start=1):
            self.logger.info(
                f"'{self.vendor_id}' - auth sequence {i}/{len(login_steps) + 1} {step['name']} | {step['url']}"
            )
            response = download_instance(
                link=step["url"], method=step['method'], data=step['form'], headers=None, session=session
            )
            if not response:
                message = f"'{self.vendor_id}' '{step['name']}' -  connection error | terminating service"
                event_message = 'vendor authentication error - please test your credentials in the vendor ' \
                                'configuration page'
                self.logger.error(message)
                raise ApiAuthenticationError(url=step['url'], internal_message=message, event_message=event_message)
            if i == len(login_steps):
                self.logger.info(f"'{self.vendor_id}' - auth sequence {len(login_steps) + 1}/{len(login_steps) + 1} "
                                 f"generating API tokens | {gen_token_url}")
                authorize_token = response.url.split("code=")[-1]
                token_request_form["code"] = authorize_token

        tokens_response = download_instance(
            session=session, link=gen_token_url, method="POST", json=token_request_form, data={}, headers=None
        )
        if not tokens_response:
            message = f"'{self.vendor_id}' generating API tokens -  connection error | terminating service"
            event_message = 'vendor authentication error - ' \
                            'please test your credentials in the vendor configuration page'
            self.logger.error(message)
            raise ApiAuthenticationError(url=gen_token_url, internal_message=message, event_message=event_message)
        try:
            data = json.loads(tokens_response.text)
            if not data:
                message = f"'{self.vendor_id}' generating API tokens - empty response | terminating service"
                event_message = 'vendor authentication error - ' \
                                'please test your credentials in the vendor configuration page'
                self.logger.error(message)
                raise ApiAuthenticationError(url=gen_token_url, internal_message=message, event_message=event_message)

            self.logger.info(f"'{self.vendor_id}' - API tokens retrieved successfully")
            return data
        except json.JSONDecodeError as e:
            message = f"'{self.vendor_id}' generating API tokens - response parse error | terminating service"
            event_message = 'vendor authentication error - ' \
                            'please test your credentials in the vendor configuration page'
            self.logger.error(message)
            raise ApiResponseError(url=gen_token_url, event_message=event_message, internal_message=message) \
                from e

    def authorize_bug_access(self, netapp_user, netapp_password):
        """
        1. create a session for authorized bug access ( separated from the API token access )
        2. save the session in instance level under self.oam_session
        :return:
        """
        authorize_steps = [
            {"url": "https://mysupport.netapp.com/api/login/oam", "name": "creating OAM session", "method": "GET",
             "form": None},
            {"url": "https://login.netapp.com/oam/server/auth_cred_submit/", "name": "logging in", "method": "POST",
             "form": f"action=login&username={netapp_user}&password={netapp_password}"}
        ]
        for i, step in enumerate(authorize_steps, start=1):
            self.logger.info(
                f"'{self.vendor_id}' - auth sequence {i}/{len(authorize_steps)} {step['name']} | {step['url']}"
            )
            response = download_instance(
                link=step["url"], method=step['method'], data=step['form'], headers=None, session=self.oam_session
            )
            if not response:
                message = f"'{self.vendor_id}' '{step['name']}' -  connection error | terminating service"
                event_message = 'vendor authentication error - ' \
                                'please test your credentials in the vendor configuration page'
                self.logger.error(message)
                raise ApiAuthenticationError(url=step['url'], internal_message=message, event_message=event_message)
        self.logger.info(f"'{self.vendor_id}' - OAM session created successfully")

    def get_bugs_data(self, risks, customer_name):
        """
        get bug data from the bug API for each risk
        :param risks:
        :param customer_name:
        :return:
        """
        for risk in risks:
            self.logger.info(f"'{customer_name}' - getting bugId '{risk['bugId']}' | {risk['bug_api_url']}")
            response = download_instance(link=risk['bug_api_url'], session=self.oam_session, headers="")
            if not response:
                message = f"'{self.vendor_id}' vendor API connection error | {risk['bug_api_url']}"
                event_message = 'vendor API connection error - we are actively working on a fix'
                self.logger.error(message)
                raise ApiConnectionError(
                    url={risk['bug_api_url']}, internal_message=message, event_message=event_message
                )
            try:
                risk["bug_data"] = json.loads(response.text)
            except json.JSONDecodeError as e:
                message = f"'{self.vendor_id}' - vendor API response parse error | {risk['bug_api_url']} service"
                event_message = 'vendor API response parse error - we are actively working on a fix'
                self.logger.error(message)
                raise ApiResponseError(
                    url={risk['bug_api_url']}, event_message=event_message, internal_message=message
                ) from e
        return risks

    def attach_managed_products(self, managed_products, risk, bug_priority):
        """
        netApp risks could affect multiple BZ managedProducts and multiple SN instance for multiple netapp customers
        configured under a give netapp Account
        1. iterate over all the systems affiliated with a netapp account ( all the systems for all the configured
            customers )
        2. find a system affected by the risk
        3. assign a random managedProduct to the bug

        :param managed_products:
        :param risk:
        :param bug_priority:
        :return:
        """
        for sys_id, sys_data in self.account_systems.items():
            systems = [
                x for x in risk["systemsList"]
                if x["systemID"] == sys_id
            ]
            if systems:
                model_id = sys_data['model']
                affected_managed_products = [
                    x for x in managed_products if x.vendorData['vendorProductModelId'] == model_id
                ]
                random.shuffle(affected_managed_products)
                if affected_managed_products:
                    for p in affected_managed_products:
                        priority_match = [x for x in p.vendorPriorities if x["vendorPriority"] == bug_priority]
                        if priority_match:
                            return p
        return None

    def format_bug_entries(self, bugs, customer_name, managed_products):
        """

        :param bugs:
        :param managed_products:
        :param customer_name:
        :return:
        """
        self.logger.info(f"'{customer_name}' - formatting bug entries | {json.dumps(bugs, default=str)}")
        formatted_entries = []
        for risk in bugs:
            formatted_entry = dict()
            missing_mandatory_field = False
            # mandatory fields check
            mandatory_fields = ['bugId', 'errorDetail']
            for field in mandatory_fields:
                if not risk.get(field, None):
                    self.logger.error(
                        f"'{self.vendor_id}' - bug missing mandatory field '{field}' | "
                        f"{json.dumps(risk, default=str)}")
                    missing_mandatory_field = True
                    break
            if missing_mandatory_field:
                continue

            formatted_entry["bugId"] = str(risk["bugId"])
            formatted_entry["summary"] = risk.get('riskName', "").strip()
            formatted_entry["description"] = risk['errorDetail'].strip()

            # add optional details from the risk to the bug description
            optional_fields = [
                ('Category', 'category'),
                ('Mitigation', 'mitigation'),
                ('Mitigation Category', 'mitigationCategory'),
                ('Mitigation Action', 'mitigationAction'),
                ('Mitigation Type', 'mitigationType'),
                ('Impact Area', 'impactArea'),
                ('Impact Level', 'impactLevel'),
                ('Potential Impact', 'potentialImpact'),
                ('Workaround', 'publicWorkaround'),
                ('Affected ActiveIQ Systems', 'affectedSystems'),
                ('Risk ID', 'riskId'),
            ]
            for field in optional_fields:
                if risk.get(field[1]):
                    formatted_entry["description"] += f"\n\n{field[0]}:\n{risk.get(field[1])}"

            formatted_entry["knownFixedReleases"] = ""
            formatted_entry["bugUrl"] = risk["bugUrl"]
            formatted_entry["snCiTable"] = self.sn_table
            formatted_entry['affectedSerialNos'] = set(risk['affectedSerialNos'])

            attached_managed_product = self.attach_managed_products(
                managed_products=managed_products, bug_priority=risk["impactLevel"], risk=risk
            )
            if not attached_managed_product:
                continue

            formatted_entry["knownAffectedReleases"] = {attached_managed_product.name}
            formatted_entry["status"] = "Unspecified"
            formatted_entry["priority"] = risk.get("impactLevel").replace('best', 'Best ').title()
            formatted_entry["managedProductId"] = attached_managed_product.id
            formatted_entry["vendorId"] = self.vendor_id
            formatted_entry["vendorData"] = {
                "netAppRiskId": risk.get('riskId'),
                "bugApiUrl": risk.get('bug_api_url'),
                "vendorProductName": attached_managed_product.name
            }

            formatted_entries.append(formatted_entry)

        return formatted_entries

    def filter_risks(self, risks, customer_name):
        """
        filter risks that don't include bug information
        :param risks:
        :param customer_name:
        :return:
        """
        bug_risks = []
        for risk in risks:
            if "bug id" in risk.get("correctiveAction", "None").lower():
                root = lxml.html.fromstring(risk["correctiveAction"])
                bug_url = root.xpath("//a[contains(text(), 'Bug ID')]/@href")
                if not bug_url:
                    continue
                bug = risk
                bug["bugUrl"] = bug_url[0]
                try:
                    bug["product_slug"] = re.findall(r"(?<=/product/).*?(?=/)", bug["bugUrl"])[0]
                except IndexError:
                    self.logger.error(
                        f"'{customer_name}' regex search failed | can't parse productId from bugUrl field"
                    )
                    continue

                bug["bugId"] = bug_url[0].split("/")[-1]
                bug["bug_api_url"] = f'https://mysupport.netapp.com/api/bol-service/{bug["product_slug"]}/bugs/BURT/' \
                                     f'{bug["bugId"]}'

                bug_risks.append(bug)
        self.logger.info(f"'{customer_name}' - {len(bug_risks)}/{len(risks)} risks identified as bugs")
        return bug_risks

    def get_oath_cred(self, secret_name):
        """
        - retrieve netapp mysupport credentials from AWS Secrets Manager
        :param secret_name:
        :return:
        """
        try:
            get_secret_value_response = self.secret_manager_client.get_secret_value(
                SecretId=secret_name
            )
            if "SecretString" in get_secret_value_response:
                secret = json.loads(get_secret_value_response["SecretString"])
                if not secret.get("setting-netapp-supportUser", None):
                    raise ValueError
                return secret
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response["SecretBinary"]
            )
            return decoded_binary_secret
        except (ClientError, ValueError) as e:
            self.logger.info(str(e))
            internal_message = f"AWS secret error - '{secret_name}' is missing"
            event_message = "Vendor integration error - we are working on getting this fixed as soon as we can"
            raise ApiConnectionError(
                event_message=event_message, internal_message=internal_message,
                url=f"https://console.aws.amazon.com/secretsmanager/home?region=us-east-1#!/secret?name={secret_name}"
            ) from e

    def consume_api(self, auth_token, endpoint_url, org_name=""):
        """

        :param auth_token:
        :param endpoint_url:
        :param org_name:
        :return:
        """
        headers = {
            "accept": "application/json",
            "authorizationtoken": auth_token
        }

        response = download_instance(
            link=endpoint_url, headers=headers, data=False
        )
        if not response:
            self.logger.error(f"'{self.vendor_id}' - API connection error | {endpoint_url}")
            raise ApiConnectionError(
                url=endpoint_url, internal_message="vendor API connection error",
                event_message=f"connection to vendor api failed | {org_name if org_name else self.vendor_id}"
            )
        try:
            data = json.loads(response.text)
        except (json.JSONDecodeError, IndexError) as e:
            self.logger.error(f"'{self.vendor_id}' - API response parse error | {endpoint_url}")
            raise ApiResponseError(
                url=endpoint_url, internal_message="error parsing response - check url",
                event_message=f"connection to vendor api failed | {org_name if org_name else self.vendor_id}"
            ) from e

        return data

    def get_account_customers(self, auth_token):
        """
        get customer IDs for a NetApp Active QI client
        an Active IQ account could have multiple customers
        :return:
        """
        api_url = "https://api.activeiq.netapp.com/v1/system/list/level/customer"
        self.logger.info(f"'{self.vendor_id}' - getting Active QI customer IDs | {api_url}")
        headers = {
            "accept": "application/json",
            "authorizationtoken": auth_token
        }
        response = download_instance(
            link=api_url, headers=headers, data=False
        )
        if not response:
            raise ApiConnectionError(
                url=api_url, internal_message="vendor API connection error",
                event_message="connection to vendor api failed"
            )
        try:
            customers = json.loads(response.text)
        except (json.JSONDecodeError, IndexError) as e:
            self.logger.error(f"response parse failed - check {api_url}")
            raise ApiResponseError(
                url=api_url, internal_message="error parsing response - check url",
                event_message="connection to vendor api failed"
            ) from e
        # sum of system across all customers
        systems_count = sum([x["systemCount"] for x in customers["customers"]["list"]])
        customers_count = len(customers["customers"]["list"])
        self.logger.info(f"'{self.vendor_id}' - {customers_count}/{systems_count} managed customers / systems found")
        return customers

    def get_aws_secret_value(self, secret_name, secret_fields):
        """
        - retrieve the latest netapp ActiveIQ refresh token from AWS Secrets Manager
        :param secret_name:
        :param secret_fields:
        :return:
        """
        try:
            get_secret_value_response = self.secret_manager_client.get_secret_value(
                SecretId=secret_name
            )
            if "SecretString" in get_secret_value_response:
                secret = json.loads(get_secret_value_response["SecretString"])
                for field in secret_fields:
                    if field not in secret or not secret[field]:
                        raise ValueError(f"AWS secret error - {field} is missing or empty")
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
                "errorType": str(exception_type),
                "errorMsg": str(e),
                "source": "",
                "service": f"{str(filename)} - line {line_number}",
            }
            self.logger.error(f"AWS SecretManager error - {json.dumps(error)}")
            raise ConnectionError(
                "Vendor Credentials Secret Manager Error - we are working on getting this fixed as soon as we can"
            ) from e

    def update_aws_secret(self, value, secret_name):
        """

        :param value:
        :param secret_name:
        :return:
        """
        try:
            self.secret_manager_client.put_secret_value(
                SecretId=secret_name, SecretString=json.dumps(value)
            )
        except (ClientError, ValueError) as e:
            self.logger.info(str(e))
            internal_message = f"AWS secret error - '{secret_name}' is missing"
            event_message = "Vendor integration error - we are working on getting this fixed as soon as we can"
            raise ApiConnectionError(
                event_message=event_message, internal_message=internal_message,
                url=f"https://console.aws.amazon.com/secretsmanager/home?region=us-east-1#!/secret?name={secret_name}"
            ) from e

    def generate_error_event(
            self, exception_traceback, exception_type, error_type, event_class, resource, node, metric_name,
            description, severity, additional_info, error_message
    ):
        """

        :param exception_traceback:
        :param exception_type:
        :param error_type:
        :param event_class:
        :param resource:
        :param error_message:
        :param node:
        :param metric_name:
        :param description:
        :param severity:
        :param additional_info:
        :return:
        """
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno
        error_message = {
            "errorType": str(exception_type),
            "errorMsg": error_message,
            "source": "",
            "service": f"{str(filename)} - line {line_number}",
        }
        self.logger.error(json.dumps(error_message, default=str))
        # generate an sn event record and send to the sns topic
        sns_client = boto3.client('sns')
        event = common_service.sn_event_formatter(
            event_class=event_class, resource=resource, node=node, metric_name=metric_name, description=description,
            error_type=error_type, severity=severity, additional_info=additional_info, logger=self.logger
        )
        event_string = json.dumps({"default": json.dumps(event)})
        sns_client.publish(
            TopicArn=os.environ["SNS_TOPIC"], Subject="test", MessageStructure="json", Message=event_string
        )
