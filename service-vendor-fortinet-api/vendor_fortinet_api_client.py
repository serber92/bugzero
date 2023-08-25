#!/usr/bin/env python3
"""
created 2021-10-14
"""
import base64
import copy
import datetime
import importlib
import inspect
import json
import logging.config
import os
import queue
import re
import sys
import threading

import boto3
import lxml.html
import pytest
from botocore.exceptions import ClientError
from requests.packages import urllib3

from download_manager import download_instance
from vendor_exceptions import ApiResponseError, ApiConnectionError, VendorConnectionError, VendorResponseError

urllib3.disable_warnings()
logger = logging.getLogger()

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
common_service = importlib.import_module("service-common.python.lib.sn_utils")


class FortinetApiClient:
    """
    - a class with methods to extract data from https://docs.fortinet.com/, work with Aurora Serverless MySQL tables
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
        self.html_error_count = 0
        self.html_error_count_threshold = 10
        self.forti_os_bug_categories = set()
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
    def get_vendor_products(self):  # pragma: no cover
        """
        retrieve supported products from doc.fortinet.com
        :return:
        """
        url = "https://docs.fortinet.com/api/products"
        # self.logger.info(f"getting vendor products")
        try:
            response = download_instance(link=url, method="get", headers="")
        except json.JSONDecodeError as e:
            error_message = "connection error - check url"
            self.logger.error(error_message)
            raise ApiResponseError(
                url=url, internal_message="error_message",
                event_message="connection to vendor api failed"
            ) from e
        return json.loads(response.text)

    def parse_release_notes(self, q, product_name):
        """

        :return:
        """
        def process_entry(entry):
            """

            :param entry:
            :return:
            """
            version_bugs = {}
            entry_url = entry[-1]["url"]
            entry_version = entry[-1]["version"]
            response = download_instance(link=entry_url, headers="")
            if not response:
                self.html_error_count += 1
                self.logger.error(f"'{product_name} v{entry_version}' - download failed | {entry_url}")
                # if more errors than the allowed threshold have been tracked raise an exception ( creates a sn event )
                if self.html_error_count >= self.html_error_count_threshold:
                    self.logger.error(f"'{product_name} v{entry_version}' - download failed | {entry_url}")
                    raise VendorConnectionError(
                        url=entry_url, internal_message="vendor connection error - check url",
                        event_message="connection to vendor web page failed"
                    )
                return version_bugs.values()

            html_root = lxml.html.fromstring(response.text)

            # find known issues urls
            known_issues_url = html_root.xpath(
                "//a[contains(text(),'Known issues') or contains(text(),'Known Issues') or contains(text(),"
                "'known issues') or contains(text(),'known Issues')]/@href"
            )
            if not known_issues_url:
                self.logger.warning(
                    f"'{product_name} v{entry_version}' - can't locate known issues href in html | {entry_url}"
                )

            # find known issues urls
            resolved_issues_url = html_root.xpath(
                "//a[contains(text(),'Resolved issues') or contains(text(),'Resolved Issues') or contains(text(),"
                "'resolved issues') or contains(text(),'resolved Issues')]/@href"
            )
            if not resolved_issues_url:
                self.logger.warning(
                    f"'{product_name} v{entry_version}' - can't locate resolved issues href in html | {entry_url}"
                )

            # find change issues urls
            change_log_url = html_root.xpath(
                "//a[contains(text(),'Change log') or contains(text(),'Change Log') or contains(text(),"
                "'change log') or contains(text(),'change Log')]/@href"
            )
            if not change_log_url:
                self.logger.warning(
                    f"'{product_name} v{entry_version}'- can't locate change log in html | {entry_url}"
                )

            change_log_url = f"https://docs.fortinet.com{change_log_url[0]}" if change_log_url else ""
            issues_urls = []
            known_issues_url = f"https://docs.fortinet.com{known_issues_url[0]}" if known_issues_url else ""
            resolved_issues_url = f"https://docs.fortinet.com{resolved_issues_url[0]}" if resolved_issues_url else ""
            if known_issues_url:
                issues_urls.append(known_issues_url)
            if resolved_issues_url:
                issues_urls.append(resolved_issues_url)

            release_note_timestamp = ""
            if issues_urls and change_log_url:
                response = download_instance(link=change_log_url, headers="")
                if not response:
                    self.logger.warning(
                        f"'{product_name} v{entry_version}' - product change log page is unreachable | {change_log_url}"
                    )
                else:
                    html_root = lxml.html.fromstring(response.text)

                    # grab top and bottom change log entries and compare their timestamps to determine which represents
                    # the first ever entry on the change log
                    first_timestamp_container = html_root.xpath(
                        "(//*[@id='content'])[1]//tbody/tr[1]//td[1]//text()"
                    )
                    last_timestamp_container = html_root.xpath(
                        "(//*[@id='content'])[1]//tbody/tr[last()]//td[1]//text()"
                    )
                    if not first_timestamp_container or not last_timestamp_container:
                        self.logger.warning(
                            f"'{product_name} v{entry_version}' - can't locate initial release note timestamp | "
                            f"{change_log_url}"
                        )
                    else:
                        first_timestamp = [x for x in first_timestamp_container if x.strip()]
                        last_timestamp = [x for x in last_timestamp_container if x.strip()]
                        timestamps = []
                        first_timestamp = self.timestamp_format(first_timestamp[0]) if first_timestamp else None
                        last_timestamp = self.timestamp_format(last_timestamp[0]) if last_timestamp else None
                        if not isinstance(first_timestamp, str):
                            if first_timestamp:
                                timestamps.append(first_timestamp)
                        if not isinstance(last_timestamp, str):
                            if last_timestamp:
                                timestamps.append(last_timestamp)
                        if timestamps:
                            # grab earliest timestamp
                            release_note_timestamp = min(timestamps)

            # get bugs ( issues ) from both the known and the resolved issues pages
            for i, url in enumerate(issues_urls, start=1):
                if not url:
                    continue

                response = download_instance(link=url, headers="")
                if not response:
                    self.logger.warning(
                        f"'{product_name} v{entry_version}' - product issues page is unreachable | {url}"
                    )
                    continue

                if response.history:
                    self.logger.warning(
                        f"'{product_name} v{entry_version}' - product issues page does not yet exist | {url}"
                    )
                    continue

                # e.g. https://docs.fortinet.com/document/fortigate/7.0.1/fortios-release-notes/236526/known-issues
                html_root = lxml.html.fromstring(response.text)
                # find bug rows
                bug_rows_xpaths = [
                    "(//*[@id='content'])[1]//*[text()='Bug ID']/ancestor::table/tbody/tr"
                ]
                bug_rows = []
                for path in bug_rows_xpaths:
                    bug_rows = html_root.xpath(path)
                    if bug_rows:
                        break

                if not bug_rows:
                    self.logger.error(f"'{product_name} v{entry_version}' - cant locate issue in html | "
                                      f"{url} ")
                    internal_message = f"failed locating issue rows using xpath '{json.dumps(bug_rows_xpaths)}'"
                    event_message = "error occurred while trying to retrieve bugs from vendor, we are actively " \
                                    "working on a fix "
                    raise VendorResponseError(internal_message=internal_message, event_message=event_message, url=url)

                # iterate rows find BugID and Description
                for row in bug_rows:
                    bug_category_container = row.xpath('(./ancestor::table/preceding-sibling::h2/text())[last()]')
                    if bug_category_container:
                        bug_category = bug_category_container[0].strip()
                        self.forti_os_bug_categories.add(bug_category)
                    else:
                        bug_category = "Model Specific"
                    bug_id_container = ""
                    bug_id_xpaths = ['./td[1]/p/text()', './td[1]/text()']
                    for path in bug_id_xpaths:
                        bug_id_container = row.xpath(path)
                        if bug_id_container:
                            break

                    if not bug_id_container:
                        self.logger.error(f"'{product_name} v{entry_version}' - cant locate bugIDs in html | "
                                          f"{url} ")
                        internal_message = f"failed locating bug IDs using xpaths - '{json.dumps(bug_id_xpaths)}'"
                        event_message = "error occurred while trying to retrieve bugs from vendor, we are actively " \
                                        "working on a fix "
                        raise VendorResponseError(
                            internal_message=internal_message, event_message=event_message, url=url
                        )

                    bug_ids = re.findall(r"\d{6,}", bug_id_container[0].strip())
                    if not bug_ids:
                        internal_message = f"'{product_name} v{entry_version}' - skipping unknown bug ID " \
                                           f"'{json.dumps(bug_id_container)}'| {url} "
                        self.logger.error(internal_message)

                    for bug_id in bug_ids:
                        bug_description = row.xpath("./td[2]//text()")
                        bug_description = [
                            entry.strip("\r\n").strip('\n').replace('\r\n', "") for entry in bug_description
                            if entry.strip()
                        ]
                        bug_summary = copy.deepcopy(bug_description)
                        if bug_category:
                            bug_description.insert(0, f"Product Element: {bug_category}\n")
                            bug_summary.insert(0, f"Product Element: {bug_category} | ")

                        if not release_note_timestamp:
                            release_note_timestamp = datetime.datetime(1900, 1, 1, 0, 00, 0)

                        # i = 2 for resolved issues urls
                        if i == 2:
                            if bug_id in version_bugs:
                                version_bugs[bug_id]["knownFixedReleases"] = entry_version
                                version_bugs[bug_id]["status"] = "Fixed"
                            else:
                                bug = {
                                    "bugId":  bug_id if bug_id else "",
                                    "description": "".join(bug_description).strip(),
                                    "summary": "".join(bug_summary).strip(),
                                    "bugUrl":  url,
                                    "status": "Fixed",
                                    "knownFixedReleases": entry_version,
                                    "release_note_timestamp": release_note_timestamp
                                    if release_note_timestamp else None,
                                    "product_name": product_name
                                }
                                version_bugs[bug_id] = bug
                        else:
                            bug = {
                                "bugId":  bug_id if bug_id else "",
                                "description": "".join(bug_description).strip(),
                                "summary": "".join(bug_summary).strip(),
                                "bugUrl":  url,
                                "status": "Open",
                                "knownAffectedReleases": entry_version,
                                "release_note_timestamp": release_note_timestamp if release_note_timestamp else None,
                                "product_name": product_name
                            }
                            version_bugs[bug_id] = bug
            return version_bugs.values()

        while not q.empty():
            queue_object = q.get()
            self.bugs.extend(process_entry(entry=queue_object))
            q.task_done()

    def release_notes_download_manager(self, release_notes_urls, product_name, threads=3):
        """
        1. download release notes html
        2. parse and follow known and resolved issues urls
        3. populate bugs
        :param release_notes_urls:
        :param product_name:
        :param threads:
        :return:
        """
        self.bugs = list()
        self.logger.info(f"'{product_name} - downloading release notes pages  | {json.dumps(release_notes_urls)}")

        q = queue.Queue()
        for i, entry in enumerate(release_notes_urls):
            q.put((i, entry))

        for i in range(threads):
            t = threading.Thread(
                target=self.parse_release_notes, args=(q, product_name)
            )
            t.start()

        q.join()

        return self.bugs

    def consolidate_bugs(self, bugs):
        """
        consolidate bug description, knownAffectedReleases, knownFixedReleases
        filter out bugs not matching vendor_statuses configured for the managed product
        :param bugs:
        :param product_name:
        :return:
        """
        self.logger.info(f"'{self.vendor_id}' - consolidating bugs")
        consolidated_bugs = dict()
        bugs = sorted(bugs, key=lambda x: (int(x["bugId"]), x['release_note_timestamp']), reverse=True)
        for bug in bugs:
            bug_id = bug["bugId"]
            bug_description = bug['description']
            version = bug.get("knownFixedReleases", bug.get("knownAffectedReleases"))
            product_name = bug['product_name']

            # create the initial bug entry
            if bug_id not in consolidated_bugs:
                release_note_timestamp = bug.get('release_note_timestamp')
                if not release_note_timestamp:
                    release_note_timestamp = datetime.datetime(1900, 1, 1, 0, 00, 0)
                consolidated_bugs[bug_id] = {
                    "bugId": bug_id,
                    "bug_urls": {bug["bugUrl"]: release_note_timestamp},
                    "description_list": [],
                    "fixed_description_list": [],
                    "summary": bug['summary'],
                    "knownAffectedReleases": [],
                    "knownFixedReleases": [],
                    "release_notes_timestamps": {
                        bug['release_note_timestamp']: (version, product_name)
                    } if bug.get('release_notes_timestamp') else {},
                    "status": bug["status"]
                }

            # update the release note timestamp and url for existing bugs
            else:
                if bug.get('release_note_timestamp') and bug["release_note_timestamp"] not in \
                        consolidated_bugs[bug_id]["release_notes_timestamps"]:
                    consolidated_bugs[bug_id]["release_notes_timestamps"][bug["release_note_timestamp"]] = \
                        (version, product_name)

                if bug["bugUrl"] not in consolidated_bugs[bug_id]["bug_urls"]:
                    release_note_timestamp = bug.get('release_note_timestamp')
                    if not release_note_timestamp:
                        release_note_timestamp = datetime.datetime(1900, 1, 1, 00, 00, 0)
                    consolidated_bugs[bug_id]["bug_urls"][bug["bugUrl"]] = release_note_timestamp

            # for resolved issues - update the bug's knownFixedReleases and the fixed release description
            if bug.get('knownFixedReleases'):
                if bug['knownFixedReleases'] not in consolidated_bugs[bug_id]['knownFixedReleases']:
                    consolidated_bugs[bug_id]['knownFixedReleases'].append(bug['knownFixedReleases'])

                fixed_in_version_description = f"\nThis bug is fixed in versions {bug['knownFixedReleases']}"

                if bug['release_note_timestamp']:
                    fixed_in_version_description += f" released on " \
                                                    f"{bug['release_note_timestamp'].strftime('%B %d, %Y')}:"
                else:
                    fixed_in_version_description += ":"

                consolidated_bugs[bug_id]["fixed_description_list"].append(
                    fixed_in_version_description
                )
                consolidated_bugs[bug_id]["fixed_description_list"].append(
                    bug_description
                )
            # for known issues - update the bug's knownAffectedReleases, the description list and the summary field
            elif bug.get('knownAffectedReleases'):
                if bug['knownAffectedReleases'] not in consolidated_bugs[bug_id]['knownAffectedReleases']:
                    consolidated_bugs[bug_id]['knownAffectedReleases'].append(bug.get('knownAffectedReleases'))
                release_notes_description = f"\nInformation from {product_name} v{bug['knownAffectedReleases']} " \
                                            f"release notes:\n{bug_description}"
                consolidated_bugs[bug_id]['description_list'].append(release_notes_description)
                consolidated_bugs[bug_id]['summary'] = bug['summary']

        # clean the consolidated bug entry, setting the earliest recollection of the bug, the vendorLastUpdatedDate
        # and the statement about the bug being fixed if relevant
        for bug_id, bug_data in consolidated_bugs.items():
            try:
                earliest_release_note_date = min(bug_data['release_notes_timestamps'])
                earliest_release_note_version = bug_data['release_notes_timestamps'][earliest_release_note_date][0]
                earliest_release_note_product_name = bug_data['release_notes_timestamps'][earliest_release_note_date][1]
                bug_data["description_list"].append(
                    f"\nThe earliest recollection of this bug is traced back to {earliest_release_note_product_name} "
                    f"v{earliest_release_note_version} released on {earliest_release_note_date.strftime('%B %d, %Y')}."
                )
            # if there are no release_notes_timestamps
            except ValueError:
                bug_data["description_list"].append(
                    f"\nThe earliest recollection of this bug is unknown."
                )

            bug_data["description"] = "\n".join(bug_data["description_list"])
            if bug_data["fixed_description_list"]:
                bug_data["description"] += "\n" + "\n".join(bug_data["fixed_description_list"])
            known_bug_urls = "\n\nFor more information:\n" + "\n".join(
                list(sorted(list(bug_data['bug_urls'].keys())))
            )
            bug_data['description'] += known_bug_urls
            # replace more than one white space
            bug_data['description'] = re.sub(r' {2,}', r' ', bug_data["description"])
            try:
                bug_data["vendorLastUpdatedDate"] = max(bug_data['release_notes_timestamps'])
            except ValueError:
                pass

            del bug_data["description_list"]
            del bug_data["fixed_description_list"]
            del bug_data["release_notes_timestamps"]
        return list(consolidated_bugs.values())

    def format_bug_entry(self, bugs, managed_product, sn_ci_filter, sn_ci_table):
        """
        format product bugs to bz bug entries
        :param bugs:
        :param managed_product:
        :param sn_ci_filter:
        :param sn_ci_table:
        :param os_version:
        :return:
        """
        formatted_bugs = list()
        # add version to to sn_ci_filter
        if sn_ci_filter:
            sn_ci_filter += f"^hardware_os_versionLIKEv{os_version}^NQhardware_os_versionLIKEV{os_version}"
        else:
            sn_ci_filter = f"hardware_os_versionLIKEv{os_version}^NQhardware_os_versionLIKEV{os_version}"

        if isinstance(bugs, dict):
            bugs = [bugs]
        for bug in bugs:
            formatted_entry = dict()
            missing_mandatory_field = False
            # mandatory fields check
            mandatory_fields = ["bugId", "description"]
            for field in mandatory_fields:
                if not bug.get(field, None):
                    self.logger.error(
                        f"'{managed_product.name} v{bug['knownAffectedReleases']}' - bug missing mandatory field "
                        f"'{field}' - {json.dumps(bug, default=str)}")
                    missing_mandatory_field = True
                    break
            if missing_mandatory_field:
                continue

            formatted_entry["bugUrl"] = max(bug["bug_urls"], key=bug["bug_urls"].get)
            if not formatted_entry["bugUrl"]:
                formatted_entry["bugUrl"] = list(bug["bug_urls"].values())[0]

            formatted_entry["knownAffectedReleases"] = ", ".join(sorted(bug["knownAffectedReleases"]))
            formatted_entry["knownFixedReleases"] = ", ".join(sorted(bug["knownFixedReleases"]))
            formatted_entry["bugId"] = str(bug["bugId"])
            formatted_entry["description"] = bug["description"].strip()
            if bug.get('vendorLastUpdatedDate'):
                formatted_entry["vendorLastUpdatedDate"] = bug["vendorLastUpdatedDate"]
            formatted_entry["summary"] = bug["summary"].strip()

            # add versions to to sn_ci_filter
            version_filter = "^NQ".join([f"firmware_versionLIKEv{x}" for x in bug["knownAffectedReleases"]])

            if sn_ci_filter:
                bug_ci_filter = f"{sn_ci_filter}^{version_filter}"
            else:
                bug_ci_filter = version_filter
            formatted_entry["snCiFilter"] = bug_ci_filter
            formatted_entry["snCiTable"] = sn_ci_table
            formatted_entry["priority"] = "Unspecified"
            formatted_entry["status"] = bug["status"]
            formatted_entry["managedProductId"] = managed_product.id
            formatted_entry["vendorId"] = self.vendor_id
            formatted_entry["vendorData"] = {
                "vendorProductName": managed_product.name
            }

            formatted_bugs.append(formatted_entry)

        return formatted_bugs

    @staticmethod
    def timestamp_format(time_str):
        """
        convert timedate strings to timedate objects
        :param time_str:
        :return:
        """
        # max 6 digit micro second
        known_formats = [
            "%B %d, %Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%a, %d %b %Y %H:%M:%S Z",
            "%a, %d %b %Y %H:%M:%SZ"
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

    def sn_sync(self, product_type, sn_api_url, sn_auth_token, sn_ci_query_base):
        """
        keep managed products software version up to date with the correlating instances in the SN instance
        run sn queries to find product version in the SN instance
        :param sn_api_url:
        :param sn_auth_token:
        :param sn_ci_query_base:
        :param product_type:
        :return:
        """

        sn_ci_query_base = f"?sysparm_query={sn_ci_query_base}"
        sn_query_url = f"{sn_api_url}/api/now/table/{product_type['service_now_ci_table']}{sn_ci_query_base}"
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
                f"'{product_type['type']}' '{product_type['service_now_ci_table']}' - {count} SN CI(s) found")
            try:
                instances = json.loads(response.text)["result"]
            except json.JSONDecodeError as e:
                raise ApiResponseError(
                    url=sn_query_url, internal_message="error parsing serviceNow response - check url",
                    event_message="ServiceNow query returned a malformed response - check ServiceNow settings"
                ) from e
            # populate query url
            for x in instances:
                x['sn_query_url'] = sn_query_url
            return instances
        self.logger.info(
            f"'{product_type['type']}' '{product_type['service_now_ci_table']}' - No SN CIs found")
        return []

    def generate_release_notes_urls(
            self, product_slug_name, product_name,
    ):
        """
        1. download the product doc landing page
        2. parse the release notes url and follow
        3. parse known/resolved issues urls for each of the product versions
        :param product_slug_name:
        :param product_name:
        :return:
        """
        product_url = f"https://docs.fortinet.com/product/{product_slug_name}"
        response = download_instance(link=product_url, headers="")
        if not response:
            raise VendorConnectionError(
                url=product_url, internal_message=f"'{product_name}' - product page is unreachable",
                event_message=f"'{product_name}' - product page is unreachable"
            )

        # e.g. https://docs.fortinet.com/product/fortigate/6.0.0
        html_root = lxml.html.fromstring(response.text)
        release_notes_url_container = html_root.xpath(
            f"//h3/a[text()='Release Notes']//ancestor::div[1]//a/@href"
        )
        if not release_notes_url_container:
            self.logger.warning(
                f"'{product_name}' - product release notes page does not exist | skipping bug lookup"
            )
            return False

        urls_cache = []
        release_notes_url = f"https://docs.fortinet.com{release_notes_url_container[0]}"
        response = download_instance(link=release_notes_url, headers="")
        if not response:
            self.logger.warning(
                f"'{product_name}' - product page is unreachable | skipping bug lookup"
            )
            return False

        html_root = lxml.html.fromstring(response.text)
        release_notes_versions = html_root.xpath(
            "//*[@class='version-dropdown']//*[@class='version-item']/a"
        )
        for entry in release_notes_versions:
            version = entry.xpath("text()")[0]
            url = f"https://docs.fortinet.com{entry.xpath('@href')[0]}"
            urls_cache.append(
                {"version": version, "url": url}
            )

        return urls_cache
