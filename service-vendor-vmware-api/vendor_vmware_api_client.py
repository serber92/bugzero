#!/usr/bin/env python3
"""
created 2021-04-28
"""
import base64
import datetime
import importlib
import json
import logging.config
import os
import re
import sys
import urllib.parse

import boto3
import lxml.html
import requests
from botocore.exceptions import ClientError
from requests.packages import urllib3

from download_manager import request_instance
from vendor_exceptions import ApiResponseError, ApiConnectionError, ServiceNotConfigured, VendorConnectionError, \
    VendorResponseError

common_service = importlib.import_module("service-common.python.lib.sn_utils")

urllib3.disable_warnings()
urllib3.disable_warnings()
logger = logging.getLogger()


class VmwareApiClient:
    """
    - a class with methods to communicate with VmWare Cloud Services API, work with Aurora Serverless MySQL tables
    - errors are logged and reported as service now events
    """

    def __init__(
            self,
            vendor_id,
            # service_now_ci_table="cmdb_ci",
    ):
        """"""
        self.logger = logger

        # ------------------------------------------------------------------------------------------------------------ #
        #                                         GLOBAL VARIABLES                                                     #
        # ------------------------------------------------------------------------------------------------------------ #
        self.earliest_execution = datetime.datetime.now()
        self.logger = logger
        self.vendor_id = vendor_id
        self.bug_ids = set()
        self.dedup_count = 0
        self.secret_manager_client = boto3.Session().client("secretsmanager")
        self.cached_kb_data = {}

    def check_collectors_health(self, service_token, org):
        """
        check the status of the Vmware Collectors for a given org
        :param service_token:
        :param org:
        :return:
        """
        status_check_url = "https://skyline.vmware.com/api/account/v1/collectors"
        self.logger.info(f"'{org['name']}' - getting collectors health status | {status_check_url}")
        headers = {"Authorization": f"Bearer {service_token}"}
        status_response = request_instance(url=status_check_url, session=False, headers=headers, post=False)
        if not status_response:
            internal_message = f"API connection error - collector health check could not be " \
                               f"completed | {json.dumps(org, default=str)}"
            self.logger.error(internal_message)
            event_message = f"'{org['name']}' Skyline services are unavailable | check the org Skyline services"
            raise ApiConnectionError(
                    url=status_check_url, internal_message=internal_message, event_message=event_message
                )
        try:
            status = json.loads(status_response.text)
            for collector in status:
                if collector["state"].lower() != "healthy":
                    internal_message = f"API connection error'  - collector health check failed | " \
                                       f"{json.dumps(status, default=str)}"
                    self.logger.error(internal_message)
                    event_message = f"'{org['name']}' - collector health check failed | check your SkyLine " \
                                    f"account for more details"
                    raise ApiConnectionError(
                        url=status_check_url, internal_message=internal_message, event_message=event_message
                    )
            self.logger.info(f"'{org['name']}' - {len(status)}/{len(status)} collectors passed health check")

        except json.JSONDecodeError as e:
            internal_message = f"'{org['name']}' API response error - collector health could not be completed | " \
                               f"{status_response.text} | {json.dumps(org, default=str)}"
            self.logger.error(internal_message)
            event_message = f"'{self.vendor_id}' API services are unavailable | we are actively monitoring the issue"
            raise ApiResponseError(
                url=status_check_url, internal_message=internal_message, event_message=event_message
            ) from e

    def get_aws_secret_value(self, secret_name, secret_fields):
        """
        retrieve vmware oath per service_secret_id ( assigned per client ) from AWS Secrets Manager
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

    def get_auth_token(self, vmware_cs_password, vmware_cs_username):
        """
        Engage in a sequence of JS session based authentication and retrieve the generated authentication token
        :param vmware_cs_username: vmware cloud services username
        :param vmware_cs_password: vmware cloud services password
        :return: auth token
        """
        # client ID is generic and representing vmware skyline webapp
        skyline_url = "https://skyline.vmware.com/apps/auth/csp/login?redirect_uri=https://skyline.vmware.com/advisor" \
                      "/csp-oauth-authorized"
        self.logger.info(f"'{self.vendor_id}' - getting skyline web app client_id | {skyline_url}")
        client_id_container = request_instance(url=skyline_url, session=False, retry=5, post=False)
        client_id = ""
        if client_id_container:
            client_id = re.findall("(?<=client_id=).*?(?=&)", client_id_container.url)

        if not client_id:
            internal_message = f"'{self.vendor_id}' vendor connection error - authentication process failed | " \
                               f"{skyline_url}"
            self.logger.error(internal_message)
            event_message = f"'{self.vendor_id}' vendor connection error | we are actively working on fix"
            raise VendorConnectionError(
                url=skyline_url, internal_message=internal_message, event_message=event_message
            )

        # create a new session
        s = requests.session()

        # save data responses
        json_data_container = {}

        # consume each url, save cookies and retrieve data with lxml when config
        urls_request_sequence_map = [
            {"url": "https://www.vmware.com/support/services/skyline.html", "url_key": False, "ignore_404": False,
             "headers": {
                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,"
                           "*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                 "Accept-Encoding": "gzip, deflate, br",
                 "Accept-Language": "en-US,en;q=0.9",
                 "Connection": "keep-alive",
                 "Host": "www.vmware.com",
                 "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
                 "sec-ch-ua-mobile": "?0",
                 "Sec-Fetch-Dest": "document",
                 "Sec-Fetch-Mode": "navigate",
                 "Sec-Fetch-Site": "none",
                 "Sec-Fetch-User": "?1",
                 "Upgrade-Insecure-Requests": "1",
                 "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/90.0.4430.212 Safari/537.36"
             },
             "message": "creating a new login session", "error_message": "can't proceed with session creation",
             "load_json": False, "use_session": True, "post_request": False, "post_form": False, "retry": 5},

            {"url": "https://console.cloud.vmware.com/csp/gateway/discovery", "url_key": False, "headers": False,
             "message": "adding discovery cookies to login session", "ignore_404": False,
             "error_message": "can't proceed with session creation", "load_json": False, "use_session": True,
             "post_request": False, "post_form": False, "retry": 5},

            {"url": f"https://console.cloud.vmware.com/csp/gateway/am/api/auth/discovery?username={vmware_cs_username}&"
                    f"state=https://skyline.vmware.com/advisor/csp-oauth-authorized&"
                    f"redirect_uri=https://skyline.vmware.com/apps/auth/csp/callback&"
                    f"client_id={client_id[0]}",
             "url_key": False, "headers": False, "ignore_404": False,
             "message": f"retrieving login config for user '{vmware_cs_username}'",
             "error_message": "can't retrieve login config", "load_json": True, "use_session": True,
             "post_request": False, "post_form": False, "retry": 5},

            {"url": "", "url_key": "idpLoginUrl", "headers": False, "ignore_404": False,
             "message": f"starting login sequence",
             "error_message": "can't retrieve login config", "load_json": False, "use_session": True,
             "post_request": False, "post_form": False, "retry": 5},

            {"url": f"https://auth.vmware.com/web/csp/enter-password?email={vmware_cs_username}", "url_key": "",
             "headers": False, "message": 'following password prompt', "ignore_404": False,
             "error_message": "can't proceed with session creation download error", "load_json": False,
             "use_session": True, "post_request": False, "post_form": False, "retry": 5},

            {"url": "https://auth.vmware.com/oam/server/auth_cred_submit?Auth-AppID=SCSP", "url_key": "",
             "headers": {
                 "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,"
                           "*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                 "accept-encoding": "gzip, deflate, br",
                 "accept-language": "en-US,en;q=0.9",
                 "cache-control": "max-age=0",
                 "content-type": "application/x-www-form-urlencoded",
                 "origin": "null",
                 "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
                 "sec-ch-ua-mobile": "?0",
                 "sec-fetch-dest": "document",
                 "sec-fetch-mode": "navigate",
                 "sec-fetch-site": "same-origin",
                 "sec-fetch-user": "?1",
                 "upgrade-insecure-requests": "1",
                 "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/90.0.4430.212 Safari/537.36"
             }, "message": 'logging in to skyline', "ignore_404": False,
             "error_message": "login failed - check credentials/login methods", "load_json": False,
             "use_session": True, "post_request": True,
             "post_form": f"username={vmware_cs_username}&password={vmware_cs_password}", "retry": 3,
             "xpaths": {
                 "saml": {"path": "//input[@name='SAMLResponse']/@value", "escape": True},
                 "relay_state": {"path": "//input[@name='RelayState']/@value", "escape": False}
             }
             },

            {"url": "https://csp-prod.vmwareidentity.com/SAAS/auth/saml/response", "url_key": "",
             "headers": {
                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,"
                           "*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                 "Accept-Encoding": "gzip, deflate, br",
                 "Accept-Language": "en-US,en;q=0.9",
                 "Cache-Control": "max-age=0",
                 "Connection": "keep-alive",
                 "Content-Type": "application/x-www-form-urlencoded",
                 "Host": "csp-prod.vmwareidentity.com",
                 "Origin": "https://auth.vmware.com",
                 "Referer": "https://auth.vmware.com/",
                 "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
                 "sec-ch-ua-mobile": "?0",
                 "Sec-Fetch-Dest": "document",
                 "Sec-Fetch-Mode": "navigate",
                 "Sec-Fetch-Site": "cross-site",
                 "Upgrade-Insecure-Requests": "1",
                 "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/90.0.4430.212 Safari/537.36"
             },
             "message": 'submitting saml/relay state payload', "ignore_404": True,
             "error_message": "login failed - check credentials/login methods", "load_json": False,
             "use_session": True, "post_request": True, "post_form": "", "save_url_key": "saml_url",
             "dynamic_form": "SAMLResponse=%s&RelayState=%s", "form_values": ("saml", "relay_state"), "retry": 3,
             },

            {"url": "", "url_key": "saml_url", "headers": "", "ignore_404": False,
             "message": 'requesting saml cookies',
             "error_message": "login failed - check credentials/login methods", "load_json": False,
             "use_session": True, "post_request": False, "post_form": "", "retry": 3
             },

            {"url": "https://skyline.vmware.com/advisor?authtype=csp", "url_key": "", "headers": "",
             "message": 'logging in to skyline advisor', "ignore_404": False,
             "error_message": "authentication error - check authentication process", "load_json": False,
             "use_session": True, "post_request": False, "post_form": "", "retry": 3
             },

            {"url": "", "url_key": "idpLoginUrl", "headers": False,
             "message": f"retrieving account config", "ignore_404": False,
             "error_message": "cant retrieve login config ", "load_json": False, "use_session": True,
             "post_request": True, "post_form": False, "retry": 5},

            {"url": "https://skyline.vmware.com/advisor?authtype=csp", "url_key": "", "headers": "",
             "message": 'retrieving auth config cookies',
             "error_message": "cant retrieve auth config cookies - check credentials/login process",
             "load_json": False, "use_session": True, "ignore_404": False,
             "post_request": True, "post_form": False, "retry": 5},

            {"url": "https://skyline.vmware.com/advisor/config", "url_key": "",
             "headers": {
                 "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;"
                           "q=0.8,application/signed-exchange;v=b3;q=0.9",
                 "accept-encoding": "gzip, deflate, br",
                 "accept-language": "en-US,en;q=0.9",
                 "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
                 "sec-ch-ua-mobile": "?0",
                 "sec-fetch-dest": "document",
                 "sec-fetch-mode": "navigate",
                 "sec-fetch-site": "cross-site",
                 "upgrade-insecure-requests": "1",
                 "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/90.0.4430.212 Safari/537.36"
             },
             "message": 'getting auth token',
             "error_message": "cant retrieve auth token - check credentials/login process",
             "load_json": True, "use_session": True, "ignore_404": False,
             "post_request": True, "post_form": False, "retry": 5},
        ]

        for stage in urls_request_sequence_map:
            # if the url is dynamic get it using the url key
            url = json_data_container[stage["url_key"]] if stage["url_key"] else stage["url"]

            # for dynamic post requests, get form values using the value keys
            if "dynamic_form" in stage:
                form_values = tuple([json_data_container[x] for x in stage["form_values"]])
                form_data = stage["dynamic_form"] % form_values
            else:
                form_data = stage['post_form']

            self.logger.info(f"'{self.vendor_id}' - {stage['message']} | {url}")
            # use session when configured
            if stage["use_session"]:
                response = request_instance(session=s, url=url, headers=stage["headers"], post=stage["post_request"],
                                            retry=stage["retry"], form_data=form_data, ignore_404=stage["ignore_404"])
            else:
                response = request_instance(session=False, url=url, headers=stage["headers"],
                                            post=stage["post_request"], form_data=form_data,
                                            retry=stage["retry"])
            if not response:
                internal_message = f"'{self.vendor_id}' - {stage['error_message']} | {url}"
                self.logger.error(internal_message)
                event_message = f"'{self.vendor_id}' Vendor Connection Error | we are actively working on fix"
                raise VendorConnectionError(
                    url=url, internal_message=internal_message, event_message=event_message
                )

            # load json request if configured
            if stage["load_json"]:
                try:
                    for k, v in json.loads(response.text).items():
                        json_data_container[k] = v
                except json.JSONDecodeError as e:
                    internal_message = f"'{self.vendor_id}' - {stage['error_message']} | {url}"
                    self.logger.error(internal_message)
                    event_message = f"'{self.vendor_id}' vendor connection error | we are actively working on fix"
                    raise VendorResponseError(
                        url=url, internal_message=internal_message, event_message=event_message
                    ) from e

            # get values from xpaths if configured
            if "xpaths" in stage:
                root = lxml.html.fromstring(response.text)
                for tag, xpath in stage["xpaths"].items():
                    try:
                        value = root.xpath(xpath["path"])[0].replace("\n", "")
                        if xpath["escape"]:
                            value = urllib.parse.quote(value)
                        json_data_container[tag] = value
                    except IndexError as e:
                        internal_message = f"'{self.vendor_id}' - {stage['error_message']} | {url}"
                        self.logger.error(internal_message)
                        event_message = f"'{self.vendor_id}' vendor response error | we are actively working on fix"
                        raise VendorResponseError(
                            url=url, internal_message=internal_message, event_message=event_message
                        ) from e

                    except lxml.html.etree.ParserError as e:
                        internal_message = f"'{self.vendor_id}' - {stage['error_message']} | {url}"
                        self.logger.error(internal_message)
                        event_message = f"'{self.vendor_id}' vendor response error | we are actively working on fix"
                        raise VendorResponseError(
                            url=url, internal_message=internal_message, event_message=event_message
                        ) from e

            # save next urls if configured
            if "save_url_key" in stage:
                json_data_container[stage["save_url_key"]] = response.url

        self.logger.info(f"'{self.vendor_id}' - auth tokens retrieved successfully")
        return [
                   json_data_container['userDetails']['token'],
                   json_data_container['userDetails']['cspAuthToken'],
                   json_data_container['accountDetails']['customerId'],
               ], s, client_id[0]

    def get_skyline_bugs(
            self, auth_token, prod_id, last_execution, org_id, org_name, morid, product_name, page_size=50
    ):
        """

        :param auth_token:
        :param prod_id:
        :param org_id:
        :param morid:
        :param org_name:
        :param page_size:
        :param product_name:
        :param last_execution:
        :return:
        """
        self.logger.info(f"'{product_name}' - '{morid}' ('{org_name}') | getting bug updates")
        headers = {
            'authorization': f"Bearer {auth_token}",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://skyline.vmware.com",
            "referer": "https://skyline.vmware.com/advisor/findings",
            "sec-ch-ua": '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/92.0.4515.107 Safari/537.36"
        }
        bugs = []
        findings = []

        # convert bugs_days_back to epoch for the filter payload
        last_execution_epoch = ""
        if last_execution:
            last_execution_epoch = int(last_execution.timestamp()) * 1000

        findings_url = f"https://skyline.vmware.com/api/account/v1/findings/rule"
        # get findings based on morid ( managed object reference )
        findings_response = request_instance(
            url=findings_url,
            post=True,
            json=self.bug_search_filters(
                page=1, page_size=page_size, first_seen=last_execution_epoch, morid=morid),
            headers=headers,
            session=False,
            retry=3
        )
        if not findings_response:
            internal_message = f"'{product_name}' - host '{morid}' | bug retrieval failed | {findings_url} "
            event_message = f"'{self.vendor_id} - API connection error | we are actively working on a fix'"
            self.logger.info(internal_message)
            raise ApiConnectionError(
                event_message=event_message, internal_message=internal_message, url=findings_url
            )
        try:
            findings_response = json.loads(findings_response.text)
        except json.JSONDecodeError as e:
            internal_message = f"'{product_name}' - host '{morid}' | bug retrieval failed | {findings_url} "
            event_message = f"'{self.vendor_id} - API response error | we are actively working on a fix'"
            self.logger.info(internal_message)
            raise ApiResponseError(
                event_message=event_message, internal_message=internal_message, url=findings_url
            ) from e

        findings.extend(findings_response["ruleList"])
        total_findings = findings_response["totalCount"]

        # iterate pages if more findings exist
        if total_findings > page_size:
            for i, _ in enumerate(range(page_size, total_findings + 1, page_size), start=2):
                self.logger.info(
                    f"orgId '{org_id}' - productId '{morid}' getting available skyline findings - page {i}"
                )
                findings_response = requests.post(
                    url=findings_url,
                    json=self.bug_search_filters(page=i, page_size=page_size, first_seen=last_execution_epoch,
                                                 morid=morid),
                    headers=headers,
                )
                if not findings_response:
                    internal_message = f"'{product_name}' - host '{morid}' | bug retrieval failed | {findings_url} "
                    event_message = f"'{self.vendor_id} - API connection error | we are actively working on a fix'"
                    self.logger.info(internal_message)
                    raise ApiConnectionError(
                        event_message=event_message, internal_message=internal_message, url=findings_url
                    )
                try:
                    findings_response = json.loads(findings_response.text)
                except json.JSONDecodeError as e:
                    internal_message = f"'{product_name}' - host '{morid}' | bug retrieval failed | {findings_url} "
                    event_message = f"'{self.vendor_id} - API response error | we are actively working on a fix'"
                    self.logger.info(internal_message)
                    raise ApiResponseError(
                        event_message=event_message, internal_message=internal_message, url=findings_url
                    ) from e

                findings.extend(findings_response["ruleList"])

        # filter cve/vmsa bugs and get kb data from the kb api
        for item in findings:
            if '-cve-' in item["ruleDisplayName"].lower() or 'vmsa' in item["ruleDisplayName"].lower():
                self.logger.info(f"'{product_name}' - skipping CVE bug | {json.dumps(item, default=str)}")
                continue
            kb_id_container = re.findall(r'(?<=KB#)\d+', item['ruleDisplayName'])
            if not kb_id_container:
                self.logger.error(f"'{product_name}' {item['ruleDisplayName']} - cant find a kbId in findings | "
                                  f"{json.dumps(item, default=str)}")
                continue

            kb_data = self.get_kb_data(kb_id=kb_id_container[0], product_name=product_name)

            # convert kb and finding data to a bug entry
            bug = dict()
            bug["vendorLastUpdatedDate"] = datetime.datetime.strptime(
                kb_data["meta"]['articleInfo']['lastModifiedDate'][:10], "%Y-%m-%d"
            )
            bug["vendorCreatedDate"] = datetime.datetime.strptime(
                kb_data["meta"]['articleInfo']['lastModifiedDate'][:10], "%Y-%m-%d"
            )

            bug["managedProductId"] = prod_id
            bug["versions"] = kb_data["meta"]["articleProducts"]["relatedVersions"] \
                if 'articleProducts' in kb_data["meta"] and 'relatedVersions' in kb_data["meta"]['articleProducts'] \
                else []

            known_affected_releases = []
            if kb_data["meta"].get('articleProducts') and kb_data["meta"]['articleProducts'].get('relatedVersions'):
                known_affected_releases.extend(kb_data["meta"]["articleProducts"]["relatedVersions"])
            if bug["versions"]:
                for x in bug["versions"]:
                    if x not in known_affected_releases:
                        known_affected_releases.append(x)

            bug["knownAffectedReleases"] = ", ".join(known_affected_releases)
            bug["bugId"] = item["ruleId"]
            bug["bugUrl"] = f"https://kb.vmware.com/s/article/{kb_id_container[0]}"
            bug["summary"] = item['ruleDescription']
            bug["processed"] = 0
            bug["priority"] = item['severity']
            bug["vendorId"] = self.vendor_id
            bug["description"] = [f"<h4>{k}</h4><div>{v}</div>" for x in kb_data["content"] for k, v in x.items()]
            bug["description"] = "".join([x.replace(u"\xa0", "") for x in bug['description']])
            bug["vendorData"] = {
                "morIds": set(),
                "kbId": kb_id_container[0],
                "vendorFirstSeenDate": datetime.datetime.strptime(
                    kb_data["meta"]['articleInfo']['lastModifiedDate'][:10], "%Y-%m-%d"
                ).strftime("%Y-%m-%d"),
                "recommendations": item["recommendations"],
                "bugCategoryName": item["categoryName"],
                "findingTypes": item["findingTypes"],
                "ruleImpact": item["ruleImpact"],
                "totalAffectedInstances": item['totalObjectsCount'],
                "supportCases": kb_data["meta"]['articleInfo']['articleCaseAttachCount'],
                "articleViews": kb_data["meta"]['articleInfo']['articleViews'],
                "versions": set()
            }
            bugs.append(bug)

        return bugs

    def get_auth(self, vendor_id, vmware_config):
        """

        :param vendor_id:
        :param vmware_config:
        :return:
        """
        logger.info(f"'{vendor_id}' - starting authentication process")

        # get the vmware skylineAuth from AwsSecretManager
        if "secretId" not in vmware_config or not vmware_config['secretId']:
            internal_message = "secretId is missing or empty - the tenant has not configured vmware skyline in the UI"
            self.logger.info(internal_message)
            event_message = f"{vendor_id} login credentials are not configured | see vendor configuration page for " \
                            f"more details"
            raise ServiceNotConfigured(
                internal_message=internal_message, event_message=event_message, service_id='secretId'
            )

        vmware_service_cred = self.get_aws_secret_value(
            secret_name=vmware_config["secretId"],
            secret_fields=["username", "password"]
        )

        # generate vmware cloud services API skyline token and service token
        tokens, session, client_id = self.get_auth_token(
            vmware_cs_password=vmware_service_cred["password"],
            vmware_cs_username=vmware_service_cred["username"],
        )
        if not tokens:
            internal_message = "vmware authentication failed - skyline token could not be generated"
            self.logger.info(internal_message)
            event_message = f"{vendor_id} login authentication failed | see vendor configuration page for more details"
            raise ApiConnectionError(event_message=event_message, internal_message=internal_message, url="")

        return vmware_service_cred, tokens, session, client_id

    def get_org_tokens(self, authenticated_session, org, vmware_cs_username, client_id):
        """
        switch session and auth tokens to a given orgId
        :param authenticated_session:
        :param org:
        :param client_id:
        :param vmware_cs_username:
        :return:
        """
        # save data responses
        json_data_container = {}
        urls_request_sequence_map = [
            {"url": f"https://console.cloud.vmware.com/csp/gateway/am/api/auth/discovery?"
                    f"username={vmware_cs_username}&"
                    f"state=https://skyline.vmware.com/advisor/csp-oauth-authorized&"
                    f"redirect_uri=https://skyline.vmware.com/apps/auth/csp/callback&client_id={client_id}&"
                    f"orgLink={org['orgRefLink']}",
             "url_key": "", "headers": "", "message": f"switching to org",
             "error_message":
                 f"can't switch to configured org {org['orgId']} - check credentials/org id",
             "load_json": True, "ignore_404": False,
             "use_session": True, "post_request": False, "post_form": "", "retry": 3,
             },

            {"url": "", "url_key": "idpLoginUrl", "headers": False,
             "message": f"retrieving org configuration", "ignore_404": False,
             "error_message": "cant retrieve login config ", "load_json": False, "use_session": True,
             "post_request": True, "post_form": False, "retry": 5},

            {"url": "https://skyline.vmware.com/advisor?authtype=csp", "url_key": "", "headers": "",
             "message": f"retrieving org auth config cookies",
             "error_message": "cant retrieve auth config cookies - check credentials/login process",
             "load_json": False, "use_session": True, "ignore_404": False,
             "post_request": True, "post_form": False, "retry": 5},

            {"url": "https://skyline.vmware.com/advisor/config", "url_key": "",
             "headers": {
                 "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;"
                           "q=0.8,application/signed-exchange;v=b3;q=0.9",
                 "accept-encoding": "gzip, deflate, br",
                 "accept-language": "en-US,en;q=0.9",
                 "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
                 "sec-ch-ua-mobile": "?0",
                 "sec-fetch-dest": "document",
                 "sec-fetch-mode": "navigate",
                 "sec-fetch-site": "cross-site",
                 "upgrade-insecure-requests": "1",
                 "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/90.0.4430.212 Safari/537.36"
             },
             "message": f"getting org auth tokens",
             "error_message": "cant retrieve auth token - check credentials/login process",
             "load_json": True, "use_session": True, "ignore_404": False,
             "post_request": True, "post_form": False, "retry": 5},
        ]
        for stage in urls_request_sequence_map:
            # if the url is dynamic get it using the url key
            url = json_data_container[stage["url_key"]] if stage["url_key"] else stage["url"]

            # for dynamic post requests, get form values using the value keys
            if "dynamic_form" in stage:
                form_values = tuple([json_data_container[x] for x in stage["form_values"]])
                form_data = stage["dynamic_form"] % form_values
            else:
                form_data = stage['post_form']

            self.logger.info(f"'{org['name']}' - {stage['message']} | {url}")
            # use session when configured
            if stage["use_session"]:
                response = request_instance(
                    session=authenticated_session, url=url, headers=stage["headers"], post=stage["post_request"],
                    retry=stage["retry"], form_data=form_data, ignore_404=stage["ignore_404"]
                )
            else:
                response = request_instance(
                    session=False, url=url, headers=stage["headers"], post=stage["post_request"], form_data=form_data,
                    retry=stage["retry"]
                )
            if not response:
                internal_message = f"'{self.vendor_id}' - {stage['error_message']} | {url}"
                self.logger.error(internal_message)
                event_message = f"'{self.vendor_id}' Vendor Connection Error | we are actively working on fix"
                raise VendorConnectionError(
                    url=url, internal_message=internal_message, event_message=event_message
                )

            # load json request if configured
            if stage["load_json"]:
                try:
                    for k, v in json.loads(response.text).items():
                        json_data_container[k] = v
                except json.JSONDecodeError as e:
                    internal_message = f"'{self.vendor_id}' - {stage['error_message']} | {url}"
                    self.logger.error(internal_message)
                    event_message = f"'{self.vendor_id}' vendor connection Error | we are actively working on fix"
                    raise VendorResponseError(
                        url=url, internal_message=internal_message, event_message=event_message
                    ) from e

            # get values from xpaths if configured
            if "xpaths" in stage:
                root = lxml.html.fromstring(response.text)
                for tag, xpath in stage["xpaths"].items():
                    try:
                        value = root.xpath(xpath["path"])[0].replace("\n", "")
                        if xpath["escape"]:
                            value = urllib.parse.quote(value)
                        json_data_container[tag] = value
                    except IndexError as e:
                        self.logger.error(
                            f"{stage['error_message']} - {url}"
                        )
                        internal_message = f"'{self.vendor_id}' - {stage['error_message']} | {url}"
                        self.logger.error(internal_message)
                        event_message = f"'{self.vendor_id}' vendor response error | we are actively working on fix"
                        raise VendorResponseError(
                            url=url, internal_message=internal_message, event_message=event_message
                        ) from e

                    except lxml.html.etree.ParserError as e:
                        self.logger.error(
                            f"{stage['error_message']} - {url}"
                        )
                        internal_message = f"'{self.vendor_id}' - {stage['error_message']} | {url}"
                        self.logger.error(internal_message)
                        event_message = f"'{self.vendor_id}' vendor response error | we are actively working on fix"
                        raise VendorResponseError(
                            url=url, internal_message=internal_message, event_message=event_message
                        ) from e

            # save next urls if configured
            if "save_url_key" in stage:
                json_data_container[stage["save_url_key"]] = response.url

        self.logger.info(f"'{org['name']}' - auth tokens retrieved successfully")
        return [
            json_data_container['userDetails']['token'],
            json_data_container['userDetails']['cspAuthToken'],
            json_data_container['accountDetails']['customerId'],
        ]

    def get_inventory(self, auth_token, org):
        """

        :param auth_token:
        :param org:
        :return:
        """
        org_id = org["orgRefLink"].split("/")[-1]
        inventory_url = f"https://skyline.vmware.com/apps/api/inventory/latest/account/{org_id}/inventory/?type=CLUSTER"
        self.logger.info(f"'{org['name']}' - getting org inventory | {inventory_url}")
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = request_instance(
            url=inventory_url, headers=headers, retry=3, session=False, post=False, ignore_404=True
        )
        if not response:
            internal_message = f"'{self.vendor_id}' API connection error - product inventory could not be retrieved" \
                               f" | {org['name']}"
            self.logger.error(internal_message)
            event_message = f"'{self.vendor_id}' - API services are unavailable for {org['name']} | we are actively " \
                            f"monitoring the issue"
            raise ApiConnectionError(
                url=inventory_url, internal_message=internal_message, event_message=event_message
            )
        try:
            inventory = json.loads(response.text)
            if not inventory:
                internal_message = f"'{self.vendor_id}' API response error  - product inventory is empty for " \
                                   f"{org['name']}"
                self.logger.error(internal_message)
                event_message = f"'{self.vendor_id}' product inventory is empty for {org['name']} | check your " \
                                f"Skyline account for more details"
                raise ApiConnectionError(
                    url=inventory_url, internal_message=internal_message, event_message=event_message
                )
            if inventory.get('errorCode'):
                internal_message = f"'{org['name']}' - API connection error for {org['name']} | " \
                                   f"{inventory.get('errorCode')}"
                self.logger.error(internal_message)
                event_message = f"'{self.vendor_id}' - org '{org['name']}' is not configured properly | check " \
                                f"your Skyline account for more details"
                raise ApiConnectionError(
                    url=inventory_url, internal_message=internal_message, event_message=event_message
                )

            return inventory

        except json.JSONDecodeError as e:
            internal_message = f"'{self.vendor_id}' API response error - product inventory could not be retrieved | " \
                               f"{inventory_url} | "
            self.logger.error(internal_message)
            event_message = f"'{self.vendor_id}' API services are unavailable | we are actively monitoring the issue"
            raise ApiResponseError(
                url=inventory_url, internal_message=internal_message, event_message=event_message
            ) from e

    def get_account_organizations(self, service_token):
        """
        retrieve a list of available organizations managed by a VMware account
        :return:
        """
        orgs_endpoint = "https://console.cloud.vmware.com/csp/gateway/am/api/loggedin/user/orgs?expand=1"
        self.logger.info(f"'{self.vendor_id}' - getting skyline account organizations | {orgs_endpoint}")
        headers = {"Authorization": f"Bearer {service_token}"}
        response = request_instance(url=orgs_endpoint, session=False, headers=headers, post=False)
        if not response:
            error_message = f"{self.vendor_id}' - vendor API connection error | {orgs_endpoint}"
            self.logger.error(error_message)
            raise ApiConnectionError(
                url=orgs_endpoint, internal_message=error_message,
                event_message="a connection to the vendor API could not be established - we are actively working on"
                              " a fix"
            )
        try:
            account_organizations = json.loads(response.text)
            return account_organizations
        except json.JSONDecodeError as e:
            error_message = f"{self.vendor_id}' - cant parse response json | {response.text} | {orgs_endpoint} "
            raise ApiResponseError(
                url=orgs_endpoint, internal_message=error_message,
                event_message="a connection to the vendor API could not be established - we are actively working on"
                              " a fix"
            ) from e

    def filter_bugs(self, bugs, product_priorities, product_name, host):
        """
        # filter out bugs based on config managed product priorities
        :param bugs:
        :param product_priorities:
        :param product_name:
        :param host:
        :return:
        """
        filtered_bugs = []
        self.logger.info(f"'{product_name}' - '{host['id']}' ('{host['orgName']}') | filtering bugs by priority")
        for bug in bugs:
            if bug["priority"] not in product_priorities:
                self.logger.info(
                    f"'{product_name}' - '{host['id']}' ('{host['orgName']}') | skipping bug '{bug['bugId']}' "
                    f"with a non-relevant priority '{bug['priority']}'")
                continue

            # convert sbPriority value to label
            bug["priority"] = bug["priority"].title()
            filtered_bugs.append(bug)
        return filtered_bugs

    def format_sn_filters(self, bugs, managed_product, service_now_table, sn_ci_query_base):
        """
        add snCiFilter and snCiTable
        :param bugs:
        :param managed_product:
        :param service_now_table:
        :param sn_ci_query_base:
        :return:
        """
        self.logger.info(f"'{managed_product.name}' - generating SN query filter")
        if sn_ci_query_base:
            sn_ci_query_base = f"{sn_ci_query_base}^"
        for bug in bugs:
            bug["snCiTable"] = service_now_table
            # convert version/morIds fields from set to list
            bug["vendorData"]["versions"] = sorted(list(bug["vendorData"]["versions"]))
            bug["vendorData"]["morIds"] = sorted(list(bug["vendorData"]["morIds"]))

            if bug["vendorData"].get("versions"):
                bug["snCiFilter"] = f"{sn_ci_query_base}api_versionIN" \
                                    f"{','.join(bug['vendorData']['versions'])}"
            elif bug["vendorData"].get("morIds"):
                bug["snCiFilter"] = f"{sn_ci_query_base}os=ESX^moridIN" \
                                    f"{','.join(bug['vendorData']['morIds'])}"
        return bugs

    def get_kb_data(self, kb_id, product_name):
        """
        retrieve bug information from services api using the bug doc id
        :param kb_id:
        :param product_name:
        :return:
        """
        url = f"https://kb.vmware.com/services/apexrest/v1/article?docid={kb_id}&lang=en_us"
        if kb_id in self.cached_kb_data:
            return self.cached_kb_data[kb_id]
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
                      ",application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "sec-ch-ua": '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/92.0.4515.131 Safari/537.36"
        }
        self.logger.info(
            f"'{product_name}' - getting kb data from kb API | {json.dumps({'kbId': kb_id, 'url': url}, default=str)}"
        )
        response = request_instance(url=url, session=False, headers=headers, post=False)
        if not response:
            internal_message = f"'{product_name}' - kb data retrieval failed | " \
                               f"{json.dumps({'kbId': kb_id, 'url': url}, default=str)}"
            event_message = f"'{self.vendor_id} - API connection error | we are actively working on a fix'"
            self.logger.info(internal_message)
            raise ApiConnectionError(
                event_message=event_message, internal_message=internal_message, url=url
            )
        try:
            self.cached_kb_data[kb_id] = json.loads(response.text)
        except json.JSONDecodeError as e:
            internal_message = f"'{product_name}' - kb data retrieval failed | " \
                               f"{json.dumps({'kbId': kb_id, 'url': url}, default=str)}"
            event_message = f"'{self.vendor_id} - API response error | we are actively working on a fix'"
            self.logger.info(internal_message)
            raise ApiResponseError(
                event_message=event_message, internal_message=internal_message, url=url
            ) from e

        return self.cached_kb_data[kb_id]

    @staticmethod
    def bug_search_filters(page, page_size, first_seen, morid):
        """

        :param page:
        :param page_size:
        :param first_seen:
        :param morid:
        :return:
        """
        return {
            "searchTerm": "",
            "filter": {
                "fieldToValuesMap": [
                    {
                        "type": "LIST",
                        "fieldName": "categoryName",
                        "listValues": []
                    },
                    {
                        "type": "LIST",
                        "fieldName": "severity",
                        "listValues": []
                    },
                    {
                        "type": "LIST",
                        "fieldName": "recommendationType",
                        "listValues": []
                    },
                    {
                        "type": "RANGE",
                        "fieldName": "ruleFirstSeenAt",
                        "rangeValues": {
                            "toValue": "null",
                            "fromValue": first_seen if first_seen else "null"
                        }
                    },
                    {
                        "type": "LIST",
                        "fieldName": "deploymentTagsType",
                        "listValues": []
                    }
                ],
                "objectIdList": [morid],
                "sourceIdList": [],
                "muted": False,
                "ruleComplexities": [
                    "BASIC",
                    "ADVANCED"
                ]
            },
            "sort": {
                "sortBy": "SEVERITY",
                "asc": True
            },
            "page": {
                "pageNumber": page,
                "pageSize": page_size
            }
        }

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
