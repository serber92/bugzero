#!/usr/bin/env python3
"""
created 2021-10-14
"""
import base64
import datetime
import importlib
import inspect
import json
import logging.config
import math
import os
import re
import sys
import threading
import urllib.parse
from collections import OrderedDict
from queue import Queue

import boto3
import lxml.html
import pytest
from botocore.exceptions import ClientError
from requests.packages import urllib3

from download_manager import download_instance
from vendor_exceptions import ApiResponseError, ApiConnectionError, VendorResponseError, VendorConnectionError

urllib3.disable_warnings()
logger = logging.getLogger()

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
common_service = importlib.import_module("service-common.python.lib.sn_utils")


class VeeamApiClient:
    """
    - a class with methods to extract data from https://www.veeam.com/services/kb-articles, work with Aurora Serverless
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
        self.kb_base_url = "https://www.veeam.com{}"
        self.sn_table = "cmdb_ci_spkg"
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

    def parse_kb_html(self, kb, html, managed_product):
        """
        parse bug data fields from a kb html page
        :param html:
        :param kb:
        :param managed_product:
        :return:
        """
        # remove from tree
        remove_elements_xpath = OrderedDict({
            "kb_header": {
                "xpath": "//h1",
            },
            "veeam_feedback": {
                "xpath": '//*[@class="veeam-text__open-universal-form"]/..',
            },
        })
        fields_xpath = OrderedDict({
            "description": {
                "is_mandatory": True, "xpath": '//div[contains(@class, "aem-GridColumn--default--9")]//text()',
                "multiple_elements": True, "delimiter": "", "is_date_value": False
            },
            "vendorCreatedDate": {
                "is_mandatory": True,
                "xpath": '//td[contains(text(),"Published:")]/following-sibling::td[contains(@class, "value")]//text()',
                "multiple_elements": False, "delimiter": None, "is_date_value": True
            },
            "vendorLastUpdatedDate": {
                "is_mandatory": True,
                "xpath": '//td[contains(text(),"Last Modified:")]/following-sibling::td[contains(@class, "value")]//'
                         'text()',
                "multiple_elements": False, "delimiter": None, "is_date_value": True
            }
        })

        # create an lxml parser object
        root = lxml.html.fromstring(html)
        product_affected_releases = [
            x["versionName"].replace(x["name"], "").strip() for x in kb["product"]
            if x.get('versionName') and x["name"] in x["versionName"]
        ]
        additional_affected_releases = dict()
        for x in kb["product"]:
            product_name = self.html_string_cleaner(x["name"])
            if product_name not in additional_affected_releases:
                additional_affected_releases[product_name] = []
            if x.get("versionName"):
                additional_affected_releases[product_name].append(
                    f'{x["versionName"].replace(product_name, "")}'.strip()
                )

        kb_entry = {
            "bugId": kb["id"],
            "summary": kb["title"],
            "bugUrl": self.kb_base_url.format(kb["url"]),
            "priority": "unspecified",
            "vendorId": self.vendor_id,
            "knownAffectedReleases": additional_affected_releases,
            "productVersions": product_affected_releases,
            'managedProduct': managed_product.id,
        }

        # remove elements from the html tree:
        for _fields, settings in remove_elements_xpath.items():
            for kb_row in root.xpath(settings["xpath"]):
                kb_row.getparent().remove(kb_row)

        for field, settings in fields_xpath.items():
            value_container = root.xpath(settings["xpath"])
            if not value_container and settings["is_mandatory"]:
                # keep count for parse error
                self.kb_info_parse_errors += 1
                self.kb_failed_urls.append(kb["url"])
                self.logger.error(f"'{managed_product.name} '{kb['id']}' - missing mandatory field '{field}' | "
                                  f"{self.kb_base_url.format(kb['url'])}")
                return False
            if settings["multiple_elements"]:
                value = ""
                for x in value_container:
                    text = re.sub(r" {2,}", r"", x)
                    value += text
                value = re.sub(r"\n{2,}", r"\n", value).strip()
            else:
                value = value_container[0].strip()
                if settings["is_date_value"]:
                    value = self.timestamp_format(value)

            kb_entry[field] = value
        return kb_entry

    def format_bug_entry(self, kb_entry, managed_product):
        """
        format product bugs to bz bug entries
        :param kb_entry:
        :param managed_product:
        :return:
        """
        # add version to to sn_ci_filter
        formatted_entry = dict()
        missing_mandatory_field = False
        # mandatory fields check
        mandatory_fields = ["bugId", "description"]
        for field in mandatory_fields:
            if not kb_entry.get(field, None):
                self.logger.error(
                    f"'{managed_product.name}' - bug missing mandatory field '{field}' | "
                    f"{json.dumps(kb_entry, default=str)}")
                missing_mandatory_field = True
                break
        if missing_mandatory_field:
            return False

        formatted_entry["bugId"] = str(kb_entry["bugId"])
        formatted_entry["description"] = kb_entry["description"].strip()
        formatted_entry["vendorLastUpdatedDate"] = kb_entry["vendorLastUpdatedDate"]
        formatted_entry["vendorCreatedDate"] = kb_entry["vendorCreatedDate"]
        formatted_entry["knownAffectedReleases"] = kb_entry.get("knownAffectedReleases", None)
        formatted_entry["productVersions"] = kb_entry.get("productVersions", None)
        formatted_entry["summary"] = kb_entry["summary"].strip()
        formatted_entry["bugUrl"] = kb_entry["bugUrl"]
        formatted_entry["priority"] = "Unspecified"
        formatted_entry["managedProductId"] = managed_product.id
        formatted_entry["vendorId"] = self.vendor_id
        formatted_entry["vendorData"] = {}

        return formatted_entry

    @staticmethod
    def generate_sn_filter(product_name, versions):
        """
        generate an sn filter for a given product with or without versions
        :param product_name:
        :param versions:
        :return:
        """
        versions = [f"^versionSTARTSWITH{x}." for x in versions]
        if versions:
            product_sn_filter = f"nameSTARTSWITH{product_name}{''.join(versions)}"
        else:
            product_sn_filter = f"nameSTARTSWITH{product_name}"
        return product_sn_filter

    def filter_bugs(self, managed_product, bugs, bugs_days_back, sn_ci_query_base):
        """
        1. filter bugs older then now - bugs_days_back
        2. filter bugs based on productVersions
        3. include bugs without productVersions ( affecting the product level regardless of version )
        3. filter out 'How To' KBs ( kb['summary'] starts with 'How To')
        :param managed_product:
        :param bugs:
        :param bugs_days_back:
        :param sn_ci_query_base:
        :return:
        """
        if sn_ci_query_base:
            sn_ci_query_base = f"^{sn_ci_query_base}"
        # get 'How To' KBs
        filtered_bugs = list()
        duplicated_bugs = 0
        general_kbs = []
        other = []
        blacklisted_kw = ["how to", "release notes", "release information"]
        time_threshold = datetime.datetime.utcnow() - datetime.timedelta(days=bugs_days_back + 2)
        for bug in bugs:
            if bug["bugId"] in self.bug_ids:
                duplicated_bugs += 1
                continue
            self.bug_ids.add(bug["bugId"])
            sn_filter_entries = set()
            if bug['vendorCreatedDate'] < time_threshold and bug['vendorLastUpdatedDate'] < time_threshold:
                other.append(bug)
                continue

            verified = False
            if [
                y for y in bug.get("productVersions", []) if y in managed_product.vendorData["osMajorVersions"]
            ]:
                verified = True

            if not bug.get("productVersions", None):
                verified = True

            if [y for y in blacklisted_kw if re.findall(y, bug["summary"].lower())]:
                general_kbs.append(bug)
                continue

            if verified:
                # versions for the managedProduct
                product_sn_filter = self.generate_sn_filter(
                    product_name=managed_product.name, versions=bug['productVersions']
                )
                sn_filter_entries.add(product_sn_filter)
                del bug['productVersions']

                # versions for other products
                known_affected_releases = set()
                for product, versions in bug["knownAffectedReleases"].items():
                    # skip managed product
                    product_sn_filter = self.generate_sn_filter(product_name=product, versions=versions)
                    sn_filter_entries.add(product_sn_filter)
                    for v in versions:
                        known_affected_releases.add(
                            f"{product} {v}"
                        )
                    if not versions:
                        known_affected_releases.add(
                            f"{product}"
                        )

                # join sn_filter_entries
                bug["snCiFilter"] = "^NQ".join(sn_filter_entries) + f"{sn_ci_query_base}"
                bug["snCiTable"] = self.sn_table
                bug["knownAffectedReleases"] = ", ".join(known_affected_releases)
                filtered_bugs.append(bug)

            else:
                other.append(bug)

        self.logger.info(
            f"'{managed_product.name}' - skipped {len(general_kbs)} non-bug KBs | "
            f"{json.dumps(general_kbs, default=str)}"
        )
        self.logger.info(
            f"'{managed_product.name}' - skipped {len(other)} other versions/older bugs | "
            f"{json.dumps(other, default=str)}"
        )
        if duplicated_bugs:
            self.logger.info(f"'{managed_product.name}' - skipped {duplicated_bugs} duplicated bugs")
        self.logger.info(f"'{managed_product.name}' - {len(filtered_bugs)}/{len(bugs)} bugs validated")
        return filtered_bugs

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

    def sn_sync(self, query_product, sn_api_url, sn_auth_token, sn_ci_query_base):
        """
        keep managed products software version up to date with the correlating instances in the SN instance
        run sn queries to find product version in the SN instance
        :param sn_api_url:
        :param sn_auth_token:
        :param query_product:
        :param sn_ci_query_base:
        :return:
        """
        if sn_ci_query_base:
            sn_ci_query_base = f"^{sn_ci_query_base}"
        sn_query = f"?sysparm_query={query_product['sysparm_query']}{sn_ci_query_base}"
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

    def get_kb_article_links(self, product, limit=1000):
        """
        retrieve all kb article for a given product from https://www.veeam.com/services/kb-articles
        :param product: supported product to enquire
        :param limit: default value for vendor response limit
        :return:
        """
        article_offset = 0
        page = 1
        total_pages = 1
        base_url = f"https://www.veeam.com/services/kb-articles?type=&product={product['abbr']}&searchTerm=&limit=" \
                   f"{limit}&offset={article_offset}"
        kb_articles = []
        while True:
            self.logger.info(f"'{product['name']}' - getting kb articles page {page} / {total_pages} | {base_url}")
            response = download_instance(link=base_url, headers=None)
            if not response:
                error_message = f"{product['name']}' - vendor API connection error | {base_url}"
                self.logger.error(error_message)
                raise ApiConnectionError(
                    url=base_url, internal_message=error_message,
                    event_message="a connection to the vendor API could not be established - we are actively working on"
                                  " a fix"
                )
            try:
                data = json.loads(response.text)
            except json.JSONDecodeError as e:
                error_message = f"{product['name']}' - cant parse response json | {response.text} | {base_url} "
                raise ApiResponseError(
                    url=base_url, internal_message=error_message,
                    event_message="a connection to the vendor API could not be established - we are actively working on"
                                  " a fix"
                ) from e
            try:
                kb_articles.extend(data["articles"])
                if len(kb_articles) < data["totalSize"]:
                    page += 1
                    total_pages = math.ceil(data["totalSize"] / limit)
                    article_offset += limit
                    base_url = f"https://www.veeam.com/services/kb-articles?type=&product={product['abbr']}" \
                               f"&searchTerm=&limit={limit}&offset={article_offset}"
                    continue
                break
            except KeyError as e:
                error_message = f"{product['name']}' - response missing '{e}' field | {json.dumps(data)} | " \
                                f"{base_url} "
                raise ApiResponseError(
                    url=base_url, internal_message=error_message,
                    event_message="a connection to the vendor API could not be established - we are actively working on"
                                  " a fix"
                ) from e
        return kb_articles

    def get_bugs(self, kb_entries, managed_product, bugs_days_back, sn_ci_query_base, threads=30):
        """
        crawl kb html pages and parse bug data
        :param kb_entries: kb entries for a given product
        :param threads: default value for num of multi-processing threads
        :param managed_product: supported product related to the kb entries
        :param bugs_days_back: bugs date threshold
        :param sn_ci_query_base:
        :return:
        """
        self.kb_entries_retrieved = 0
        self.total_kb_entries = len(kb_entries)
        self.bugs = []
        q = Queue()
        for kb in kb_entries:
            q.put((kb, managed_product))

        for _ in range(threads):
            t = threading.Thread(target=self.kb_html_scraper, args=(q,))
            t.start()

        q.join()

        # check for abnormal amount of parse errors:
        if self.kb_info_parse_errors > 5:
            message = f"'{self.vendor_id}' - vendor product xpath error | {json.dumps(self.kb_failed_urls)}"
            event_message = f"'{self.vendor_id}' - internal vendor website error , we are actively working on a fix"
            raise VendorResponseError(internal_message=message, event_message=event_message, url=self.kb_failed_urls[0])

        self.logger.info(
            f"'{managed_product.name}' - {self.kb_entries_retrieved}/{self.total_kb_entries} KB entries retrieved"
        )

        bugs = self.filter_bugs(
            managed_product=managed_product, bugs=self.bugs, bugs_days_back=bugs_days_back,
            sn_ci_query_base=sn_ci_query_base
        )
        return bugs

    def crawl_vendor_products(self):
        """
        crawl products list supported by the KB knowledge base
        https://www.veeam.com/knowledge-base.html
        :return:
        """

        url = "https://www.veeam.com/knowledge-base.html"
        self.logger.info(f"'{self.vendor_id}' - getting vendor products | {url}")
        response = download_instance(link=url, headers=None)
        if not response:
            message = f"'{self.vendor_id}' - vendor product download error | {url}"
            event_message = f"'{self.vendor_id}' - vendor website is unreachable, we are actively working on a fix"
            raise VendorConnectionError(url=url, internal_message=message, event_message=event_message)

        root = lxml.html.fromstring(response.text)
        products_xpath = r"//select[@name='product']/option[text()]"
        vendor_products_container = root.xpath(products_xpath)
        if not vendor_products_container:
            message = f"'{self.vendor_id}' - vendor product xpath error | {url}"
            event_message = f"'{self.vendor_id}' - internal vendor website error , we are actively working on a fix"
            raise VendorResponseError(internal_message=message, event_message=event_message, url=url)
        vendor_products = []
        for product in vendor_products_container:
            product_id = product.xpath("@value")[0]
            product_name = self.html_string_cleaner(product.xpath("text()")[0])
            vendor_products.append(
                {
                    "name": product_name,
                    "name_encoded": urllib.parse.quote(product_name),
                    "id": product_id,
                    "abbr": product_id,
                    "service_now_table": "cmdb_ci_spkg",
                    "sysparm_query": f"nameSTARTSWITH"
                                     f"{urllib.parse.quote(product_name)}",
                }
            )
        self.logger.info(
            f"'{self.vendor_id}' - {len(vendor_products)} products retrieved from vendor | "
            f"{json.dumps(vendor_products)}"
        )
        return vendor_products

    def kb_html_scraper(self, q):
        """

        :param q:
        :return:
        """
        def request(kb, managed_product):
            """
            download and parse a kb html page
            :param kb:
            :param managed_product:
            :return:
            """
            base_url = self.kb_base_url.format(kb["url"])
            response = download_instance(link=base_url, headers=None)

            if not response:
                self.logger.error(f"'{managed_product.name}' - {kb['id']} html page is unreachable | {base_url}")
                return

            kb_entry = self.parse_kb_html(html=response.text, managed_product=managed_product, kb=kb)
            if not kb_entry:
                return
            bug_entry = self.format_bug_entry(kb_entry=kb_entry, managed_product=managed_product)
            self.bugs.append(bug_entry)
            self.kb_entries_retrieved += 1
            if self.kb_entries_retrieved % 100 == 0:
                self.logger.info(
                    f"'{managed_product.name}' - {self.kb_entries_retrieved}/{self.total_kb_entries}"
                    f" KB entries retrieved"
                )

        while not q.empty():
            queue = q.get()
            request(kb=queue[0], managed_product=queue[1])
            q.task_done()

    @staticmethod
    def html_string_cleaner(html_string):
        """
        remove html tags from string
        :param html_string:
        :return:
        """
        # remove tags regex
        clean_regex = re.compile('<.*?>')
        clean_text = re.sub(clean_regex, '', html_string)
        # replace non-breaking whitespace
        return clean_text.replace("\u00A0", " ")
