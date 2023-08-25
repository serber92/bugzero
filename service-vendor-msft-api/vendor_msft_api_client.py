#!/usr/bin/env python3
"""
created 2021-12-25
"""
import base64
import copy
import datetime
import json
import logging.config
import re
import sys
import threading
from queue import Queue

import boto3
import lxml.html
import requests
from botocore.exceptions import ClientError
from requests.packages import urllib3

from download_manager import download_instance
from vendor_exceptions import ApiResponseError, ApiConnectionError, VendorConnectionError, VendorResponseError

urllib3.disable_warnings()
logger = logging.getLogger()


class MsftApiClient:
    """
    - a class with shared methods used msft services
    """
    def __init__(self, vendor_id="msft"):
        """

        :param vendor_id:
        """
        self.logger = logger
        # ------------------------------------------------------------------------------------------------------------ #
        #                                         GLOBAL VARIABLES                                                     #
        # ------------------------------------------------------------------------------------------------------------ #
        # data cache
        self.sql_bugs_dedup = set()
        self.kb_bugs = list()
        self.formatted_bugs = list()
        self.pre_formatted_sql_bugs = list()
        self.bug_kb_counter = 0

        # settings
        self.secret_manager_client = boto3.Session().client("secretsmanager")
        self.utc_now = datetime.datetime.utcnow()
        self.now = datetime.datetime.now()
        self.vendor_id = vendor_id

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
        known_formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%B %d, %Y", "%B %d,%Y", "%B %d. %Y", "%B %d.%Y"]
        fmt_time = ""
        for _, fmt in enumerate(known_formats):
            check_string = time_str[:19]
            try:
                fmt_time = datetime.datetime.strptime(check_string, fmt)
                break
            except ValueError:
                continue
        if fmt_time:
            return fmt_time
        return None

    def consolidate_bugs(self, bugs, vendor_id):
        """
        consolidate bugs and merge description, knownFixedReleases, release urls
        :param bugs:
        :param vendor_id:
        :return:
        """
        self.kb_bugs = []
        formatted_bugs = []
        consolidated_bugs = dict()
        bugs = sorted(bugs, key=lambda x: int(x["bugId"]))
        for bug in bugs:
            if bug["bugId"] not in consolidated_bugs:
                consolidated_bugs[bug["bugId"]] = [bug]
            else:
                consolidated_bugs[bug["bugId"]].append(bug)

        for bug_id, bug_entries in consolidated_bugs.items():
            bug_entry = {
                "priority": "Unspecified",
                "status": "Fixed",
                "bugId": bug_id,
                'vendorData': {"bugCategory": ""},
                "vendorId": vendor_id
            }

            sorted_entries = sorted(bug_entries, key=lambda x: x["vendorCreatedDate"])
            bug_category = list(
                {x['vendorData']['bugCategory'] for x in sorted_entries
                 if x['vendorData'].get('bugCategory', "").strip()}
            )
            bug_entry["knownFixedReleases"] = ", ".join(sorted([x["knownFixedReleases"] for x in sorted_entries]))
            bug_entry["vendorLastUpdatedDate"] = max([x['vendorLastUpdatedDate'] for x in sorted_entries])
            bug_entry["vendorCreatedDate"] = max([x['vendorCreatedDate'] for x in sorted_entries])
            bug_entry["bugUrl"] = list({x["bugKbUrl"] for x in sorted_entries if x["bugKbUrl"]})
            bug_entry['releaseUrl'] = sorted_entries[0]['releaseUrl']
            bug_entry['knownAffectedOs'] = ",".join(
                list({x['knownAffectedOs'] for x in sorted_entries if x['knownAffectedOs']})
            )
            bug_entry['vendorData']["bugCategory"] = bug_category[0] if bug_category else ""
            bug_entry['vendorData']["releaseUrl"] = bug_entry['releaseUrl']
            bug_entry['ciSysIds'] = [list(x['ciSysIds']) for x in sorted_entries]
            bug_entry['ciSysIds'] = list({x for y in bug_entry['ciSysIds'] for x in y})
            bug_entry["managedProductId"] = bug_entries[0]["managedProductId"]
            bug_entry["hasKb"] = True
            if not bug_entry["bugUrl"]:
                bug_entry["hasKb"] = False
                bug_entry["bugUrl"] = sorted_entries[0]["bugUrl"]
            else:
                bug_entry["bugUrl"] = bug_entry["bugUrl"][0]
            bug_entry["summary"] = bug_entries[0]["summary"]
            # if a kb does not for the bug, create a description from the release data
            bug_entry["description"] = ""
            if len(sorted_entries) > 1:
                bug_entry["description"] = f"Bug {bug_id} is addressed in {len(sorted_entries)} releases:\n"
                for i, entry in enumerate(sorted_entries, 1):
                    bug_entry["description"] += f"{i}. {entry['knownFixedReleases']} - {entry['releaseUrl']}\n"

                bug_entry["description"] += \
                    f"\nNotes from the latest release:\n{sorted_entries[0]['description']}\n\n"
            else:
                bug_entry["description"] += \
                    f"\nNotes from the latest release:\n{sorted_entries[0]['description']}\n" \
                    f"for more information: {sorted_entries[0]['releaseUrl']}\n"

            # bug has a kb - crawl html and enrich the bug entry
            formatted_bugs.append(bug_entry)
        if formatted_bugs:
            self.formatted_bugs = formatted_bugs
            self.logger.info(
                f"'SQL Server' - {len(bugs)} kb bugs consolidated for all existing CIs | "
                f"initiating multi-process crawl"
            )
            self.bug_kbs_crawling_manager(bugs=formatted_bugs, product_name='SQL Server')
            self.logger.info(
                f"'SQL Server' - {len(self.kb_bugs)}/{self.bug_kb_counter} kb bugs crawled"
            )
        return self.kb_bugs

    def bug_kbs_crawling_manager(self, bugs, product_name, threads=30): # pragma: no cover
        """
        multi processing crawl manager
        :return:
        """
        self.bug_kb_counter = len(bugs)
        q = Queue()
        for bug in bugs:
            q.put(bug)

        for _ in range(threads):
            t = threading.Thread(target=self.crawl_bug_kbs, args=(q, product_name))
            t.start()

        q.join()

    def crawl_bug_kbs(self, q, product_name):

        """
        crawl bug kb pages and enrich the bug_entry object
        :param q:
        :param product_name:
        :return:
        """
        def crawl_instance(bug_entry):
            # insert bugs with KB as is
            if not bug_entry["hasKb"]:
                self.kb_bugs.append(bug_entry)
                return

            response = download_instance(link=bug_entry['bugUrl'], headers="", session=False)
            # insert bugs as is if kb is not reachable
            if not response:
                self.kb_bugs.append(bug_entry)
                return
            root = lxml.html.fromstring(response.text)

            if not bug_entry.get("bugId"):
                bug_id_container = root.xpath('//meta[@name="awa-asst"]/@content')
                if not bug_id_container:
                    self.logger.error(
                        f"'{product_name}' - failed to find a bug id using xpath '//meta[@name='awa-asst']/@content' | "
                        f"{bug_entry['bugUrl']}"
                    )
                    return
                bug_entry['bugId'] = bug_id_container[0]

            kb_summary = root.xpath('//title/text()')
            if not kb_summary:
                self.logger.error(
                    f"'{product_name}' - kb summary was not found | {bug_entry['bugUrl']}"
                )
            else:
                bug_entry['summary'] = kb_summary[0]

            kb_content = ""
            kb_contents_xpaths = ['//main[@id="main"]', '//div[@id="ocArticle"]']
            for xpath in kb_contents_xpaths:
                kb_content = root.xpath(xpath)
                if not kb_content:
                    continue
                break

            # insert bug as is if kb content is missing
            if not kb_content:
                self.logger.error(
                    f"'{product_name}' - kb content was not found | {bug_entry['bugUrl']}"
                )
                self.kb_bugs.append(bug_entry)
                return

            # remove headers, footers and non-relevant sections
            article_header_footer_xpaths = [
                "//section[@aria-label='References']", "//div[contains(@class, 'ArticleFooter')]",
                "//div[contains(@class, 'page-metadata-container')]", "//section[@aria-label='More Resources']",
                "//section[@aria-label='See Also']",
            ]
            for xpath in article_header_footer_xpaths:
                for element in root.xpath(xpath):
                    element.getparent().remove(element)

            bug_entry['description'] = "\n".join([x.strip() for x in kb_content[0].xpath(".//text()") if x.strip()])

            known_affected_releases = root.xpath('//meta[@name="ms.productName"]/@content')
            if known_affected_releases:
                bug_entry['knownAffectedReleases'] = ", ".join(known_affected_releases[0].split(','))

            # for microsoft access kbs
            known_affected_items = root.xpath("//span[contains(@class, 'appliesToItem')]//text()")
            if known_affected_items:
                bug_entry['knownAffectedReleases'] = ", ".join(list(known_affected_items))
                bug_entry['knownAffectedItems'] = list(known_affected_items)
            else:
                bug_entry['knownAffectedReleases'] = ""
                bug_entry['knownAffectedItems'] = ""

            last_updated_container = root.xpath('//meta[@name="lastPublishedDate"]/@content')
            if last_updated_container:
                bug_entry['vendorLastUpdatedDate'] = self.timestamp_format(last_updated_container[0])

            published_container = root.xpath('//meta[@name="firstPublishedDate"]/@content')
            if published_container:
                bug_entry['vendorCreatedDate'] = self.timestamp_format(published_container[0])

            self.kb_bugs.append(bug_entry)
            if len(self.kb_bugs) % 100 == 0:
                self.logger.info(
                    f"'{product_name}' - {len(self.kb_bugs)}/{self.bug_kb_counter} kb bugs crawled"
                )

        while not q.empty():
            queue = q.get()
            crawl_instance(bug_entry=queue)
            q.task_done()

    def sn_sync(self, product, sn_api_url, sn_auth_token, affected_ci_query_base):
        """
        keep managed products software version up to date with the correlating instances in the SN instance
        run sn queries to find product version in the SN instance
        :param sn_api_url:
        :param affected_ci_query_base:
        :param sn_auth_token:
        :param product:
        :return:
        """
        if affected_ci_query_base:
            affected_ci_query_base = f"{affected_ci_query_base}^"
        sn_query = f"?sysparm_query={affected_ci_query_base}{product['sysparm_query']}" \
                   f"&sysparm_fields=os_version,version,sys_id"
        sn_query_url = f"{sn_api_url}/api/now/table/{product['service_now_table']}{sn_query}"
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
                f"'{product['name']}' - {count} CI(s) found for product version"
            )
            cis = json.loads(response.text)["result"]
            return cis
        return False

    def crawl_cu_kbs(self, q, managed_product, service_now_table):
        """
        1. crawl CU kbs e.g. https://support.microsoft.com/en-us/topic/cumulative-update-7-for-sql-server-2019-
          87ea390d-0def-6173-efd2-f6be8549d77d
        2a. parse bugs from html
        2b. follow bug kb urls
        3.  format bug entry
        :param q:
        :param managed_product:
        :param service_now_table:
        :return:
        """
        def instance(kb_data):
            """

            :param kb_data:
            :return:
            """
            response = download_instance(link=kb_data["kb"]["kb_url"], headers="", session=False)
            if not response:
                self.logger.warning(
                    f"'{managed_product.name}' - {kb_data['kb']['kb_id']} download failed | "
                    f"{kb_data['kb']['kb_url']}"
                )
                return

            root = lxml.html.fromstring(response.text)
            bug_rows_xpath = "//th//*[contains(text(), 'KB article') or contains(text(), 'KB Article')]//" \
                             "ancestor::table/tbody//tr"
            bug_row_elements = root.xpath(bug_rows_xpath)
            if not bug_row_elements:
                self.logger.warning(
                    f"'{managed_product.name}' - {kb_data['kb']['kb_id']} missing bug entries | "
                    f"{kb_data['kb']['kb_url']}"
                )
                return

            # use bugs table header row to determine the location of the bug columns
            bug_rows_header_xpath = "//th//*[contains(text(), 'KB article') or contains(text(), 'KB Article')]//" \
                                    "ancestor::table//th"
            bug_rows_headers = root.xpath(bug_rows_header_xpath)
            bug_td_map = {
                "bug_id": {
                    "mandatory": True,
                    "kw": ["bug"],
                    "td_index": "",
                    "value": "",
                    "href": ""
                },
                "kb_id": {
                    "kw": ["kb article"],
                    "td_index": "",
                    "mandatory": False,
                    "value": "",
                    "href": ""
                },
                "description": {
                    "kw": ["description"],
                    "td_index": "",
                    "mandatory": True,
                    "value": "",
                    "href": ""
                },
                "bug_category": {
                    "kw": ["area path", "fix area"],
                    "td_index": "",
                    "mandatory": False,
                    "value": "",
                    "href": ""
                },
                "platform": {
                    "kw": ["platform"],
                    "td_index": "",
                    "mandatory": False,
                    "value": "",
                    "href": ""
                }
            }

            for _key, item in bug_td_map.items():
                found = False
                for kw in item["kw"]:
                    if not found:
                        for i, x in enumerate(bug_rows_headers, 1):
                            header = x.xpath("./p/text()")
                            if header and kw in header[0].lower():
                                item["td_index"] = str(i)
                                found = True
                                break

            for i, entry in enumerate(bug_row_elements, 1):
                bug_data = copy.deepcopy(bug_td_map)
                for item in bug_data.keys():
                    td_index = bug_data[item]['td_index']
                    if td_index:
                        value_container = entry.xpath(f"./td[{td_index}]/p//text()")
                        href_container = entry.xpath(f"./td[{td_index}]/p//@href")
                        value = [x.strip() for x in value_container if x.strip()]
                        href = [x.strip() for x in href_container if x.strip()]
                        bug_data[item]["value"] = value[0] if value else ""
                        bug_data[item]["href"] = href[0] if href else ""

                if not bug_data["bug_id"]["value"] and not bug_data["kb_id"]["value"]:
                    self.logger.warning(
                        f"'{managed_product.name}' - bugId parsing failed (row {i}) | {kb_data['kb']['kb_url']}"
                    )
                    continue

                if not bug_data["bug_id"]["value"]:
                    bug_data["bug_id"]["value"] = bug_data["kb_id"]["value"]

                summary = "".join(bug_data["description"]["value"]).strip()
                description = summary
                bug_kb_url = ""
                if bug_data["kb_id"]["href"]:
                    bug_kb_url = bug_data["kb_id"]["href"]
                elif bug_data["description"]["href"]:
                    bug_kb_url = bug_data["description"]["href"]
                if bug_kb_url and not re.findall("^http", bug_kb_url):
                    bug_kb_url = f"https://support.microsoft.com{bug_kb_url}"

                # get the first bugId for entries that include to bugIds
                if ";" in bug_data['bug_id']['value']:
                    bug_data['bug_id']['value'] = bug_data['bug_id']['value'].split(";")[0]
                else:
                    bug_data['bug_id']['value'] = bug_data['bug_id']['value'].split(",")[0]
                try:
                    int(bug_data['bug_id']['value'])
                except ValueError:
                    bug_data['bug_id']['value'] = ""

                if not bug_data['bug_id']['value']:
                    self.logger.warning(
                        f"'{managed_product.name}' - bugId parsing failed (row {i}) | {kb_data['kb']['kb_url']}"
                    )
                    continue

                self.sql_bugs_dedup.add(bug_data['bug_id']['value'])

                sn_ci_filter = [f"sys_idSTARTSWITH{x['sys_id']}" for x in kb_data['affected_ci']]
                sn_ci_filter = "^OR".join(sn_ci_filter)

                build_version = kb_data['kb']['build_version']
                known_fixed_releases = f"{managed_product.name} {build_version}"
                bug = {
                    "bugId": bug_data['bug_id']['value'],
                    "bugKbUrl": bug_kb_url,
                    "description": description,
                    "bugUrl": bug_kb_url if bug_kb_url else kb_data['kb']['kb_url'],
                    "releaseUrl": kb_data['kb']['kb_url'],
                    "releaseName": kb_data['kb']["build_name"],
                    "buildVersion": kb_data['kb']['build_version'],
                    "buildVersionNumber": kb_data['kb']['build_version_number'],
                    "priority": "Unspecified",
                    "status": "Fixed",
                    "knownFixedReleases": known_fixed_releases,
                    "knownAffectedOs": bug_data['platform'].get('value', ""),
                    "vendorData":
                        {"bugCategory": bug_data['bug_category'].get('value')},
                    "managedProductId": managed_product.id,
                    "vendorId": self.vendor_id,
                    "summary": summary,
                    "snCiTable": service_now_table,
                    "snCiFilter": sn_ci_filter,
                    "vendorLastUpdatedDate": kb_data['kb']['release_date'],
                    "vendorCreatedDate": kb_data['kb']['release_date'],
                    "ciSysIds": [x['sys_id'] for x in kb_data['affected_ci']]
                }

                self.pre_formatted_sql_bugs.append(bug)

        while not q.empty():
            queue = q.get()
            instance(kb_data=queue)
            q.task_done()

    def parse_cu_releases(self, html_string, product, source_url, bugs_days_back_date):
        """
        parse cu release links from product build url
        :param html_string:
        :param product:
        :param source_url:
        :param bugs_days_back_date:
        :return:
        """
        out_of_scope_releases = []
        inside_scope_releases = []
        cumulative_update_kbs = []
        root = lxml.html.fromstring(html_string.text)
        # get kb rows from the main CU tables
        kb_entries = root.xpath(product["xpaths"]["kb_rows"])
        # add kb entries with build and kb url
        for i, kb in enumerate(kb_entries, 1):
            # get the build version td node
            release_date = ""
            release_date_container = kb.xpath(product["xpaths"]["release_date"])
            if release_date_container:
                release_date = self.timestamp_format(release_date_container[0])
            if not release_date:
                message = f"release date parse error - {source_url}"
                self.logger.error(message)
                raise VendorResponseError(
                    url=source_url, internal_message=message,
                    event_message="vendor data retrieve error - we are actively working on a fix"
                )

            build_version = kb.xpath(product["xpaths"]["build"])
            build_name = kb.xpath(product["xpaths"]["build_name"])
            kb_url = kb.xpath(product["xpaths"]["kb_url"])
            kb_id = kb.xpath(product["xpaths"]["kb_id"])
            if not build_version or not kb_url:
                self.logger.warning(f"'{product['name']}' - kb url / version missing in row {i} | {source_url}")
                continue

            if release_date < bugs_days_back_date:
                out_of_scope_releases.append(
                    {"release_name": f"{product['name']} {build_name[0].strip()}",
                     "release_date": release_date.strftime('%Y-%m-%d')}
                )
                continue

            inside_scope_releases.append(
                {"release_name": f"{product['name']} {build_name[0].strip()}",
                 "release_date": release_date.strftime('%Y-%m-%d')}
            )
            # remove "." to enable sort by number
            # limit to 8 digit long build version
            build_version_number = int(build_version[0].replace(".", "")[:8])
            cumulative_update_kbs.append({
                "build_version_number": build_version_number, "kb_id": kb_id[0],
                "kb_url": f"https://support.microsoft.com{kb_url[0]}" if not re.findall(r'^http', kb_url[0])
                else kb_url[0],
                "build_version": build_version[0],
                "build_name": build_name[0].strip(),
                "release_date": release_date
            })
        return out_of_scope_releases, cumulative_update_kbs, inside_scope_releases

    def get_sql_release_bugs(self, managed_product, product, active_cis, bugs_days_back, threads=30):
        """
        1. crawl sql Cumulative Update (CU) builds index page
        2. follow KBs for all the releases post the product release build
        3. parse bugs from kb pages
        4. follow bug KBs if exist
        :param managed_product:
        :param product:
        :param active_cis:
        :param threads:
        :param bugs_days_back:
        :return:
        """
        # get the Cumulative Update (CU) builds index page for the product
        self.pre_formatted_sql_bugs = []
        bugs_days_back_date = datetime.datetime.utcnow() - datetime.timedelta(days=bugs_days_back-2)
        cumulative_update_kbs = []
        filtered_kbs = {}
        out_of_scope_releases = []
        inside_scope_releases = []
        for url in product["build_urls"]:
            response = download_instance(link=url, headers="", session=False)
            if not response:
                self.logger.error(f"vendor connection error - {url}")
                raise VendorConnectionError(
                    url=url, internal_message="vendor connection error",
                    event_message="a connection to the vendor could not be established - we are actively working on a "
                                  "fix"
                )
            build_out_of_scope_release, build_cumulative_update_kbs, build_in_scope_release = self.parse_cu_releases(
                html_string=response, product=product, source_url=url, bugs_days_back_date=bugs_days_back_date
            )
            out_of_scope_releases.extend(build_out_of_scope_release)
            inside_scope_releases.extend(build_in_scope_release)
            cumulative_update_kbs.extend(build_cumulative_update_kbs)

        cumulative_update_kbs = sorted(cumulative_update_kbs, key=lambda x: x['build_version'])
        # add kbs for build versions released after the CI version
        for ci in active_cis:
            ci_build_version = int(ci['version'].replace(".", ""))
            ci_filtered_kbs = [x for x in cumulative_update_kbs if x["build_version_number"] > ci_build_version]
            for kb in ci_filtered_kbs:
                if kb["kb_id"] not in filtered_kbs:
                    filtered_kbs[kb["kb_id"]] = {
                        "kb": kb, "affected_ci_versions": {ci['version']}, "affected_ci": [
                            {"version": ci['version'], "sys_id": ci['sys_id']}
                        ]
                    }
                else:
                    filtered_kbs[kb["kb_id"]]["affected_ci_versions"].add(ci['version'])
        # crawl all cu kbs in a multi-processing queue
        if out_of_scope_releases:
            self.logger.info(
                f"'{managed_product.name}' - {len(out_of_scope_releases)} older releases skipped | "
                f"{json.dumps(out_of_scope_releases, default=str)}"
            )

        if not filtered_kbs:
            self.logger.info(
                f"'{managed_product.name}' - 0 releases found | skipping"
            )
            return []

        self.logger.info(
            f"'{managed_product.name}' - {len(inside_scope_releases)} releases found | "
            f"{json.dumps(inside_scope_releases, default=str)}"
        )

        q = Queue()
        for _kb_id, cu_kb_data in filtered_kbs.items():
            q.put(cu_kb_data)

        for _ in range(threads):
            t = threading.Thread(
                target=self.crawl_cu_kbs, args=(
                    q, managed_product, product['service_now_table'])
            )
            t.start()

        q.join()

        self.logger.info(
            f"'{managed_product.name}' - {len(self.pre_formatted_sql_bugs)} bugIds retrieved"
        )
        return self.pre_formatted_sql_bugs

    def filter_product_issues(self, managed_product, last_execution, product_issues, affected_ci_query_base):
        """
        filter service issues based on:
            1. issue type
            2. status
            3. bug date
        :param managed_product:
        :param last_execution:
        :param product_issues:
        :param affected_ci_query_base:
        :return:
        """
        self.logger.info(f"'{managed_product.name}' - filtering health issues")
        # vendor_priorities = [x['vendorPriority'].lower() for x in managed_product.vendorPriorities]
        vendor_statuses = [x.lower() for x in managed_product.vendorStatuses]
        bugs = []

        if affected_ci_query_base:
            affected_ci_query_base = f"{affected_ci_query_base}^"

        for issue in product_issues:
            issue_status = issue['Status'].get('DisplayName')
            # filter by status
            if issue_status.lower() not in vendor_statuses:
                continue
            # filter by date
            issue_last_updated_object = self.timestamp_format(issue['LastUpdated'])
            if last_execution > (issue_last_updated_object - datetime.timedelta(days=2)):
                continue

            description = ""

            description_fields = [
                {"title": "Impact", "field_name": 'ImpactDescription'},
                {"title": "Originating KB URL", 'field_name': 'OriginatingKb'},
                {"title": "Originating KB Release Date", 'field_name': 'KbReleaseDate'},
                {"title": 'Originating Build', "field_name": 'OriginatingBuild'},
                {"title": 'Resolved KB URL', "field_name": 'ResolvedKb'},
                {"title": 'Date Resolved', "field_name": 'ResolvedDate'}
            ]
            for f in description_fields:
                if issue.get(f['field_name'], ""):
                    if f['title'] in ["Originating KB URL", "Resolved KB URL"]:
                        value = f"https://support.microsoft.com/en-us/topic/{issue.get(f['field_name'])[2:]}"
                    else:
                        value = f"{issue[f['field_name']]}\n"

                    description += f"{f['title']}: {value}\n"
            description += "\nAll Updates:\n"

            known_affected_releases = set()
            for message in issue["Messages"]:
                timestamp = self.timestamp_format(
                    time_str=message['PublishedTime']
                ).strftime("%B %d, %Y %H:%M %p")
                service_message = f"------------------------------------------------------\n{timestamp}\n\n" \
                                  f"{message['MessageText']}\n"
                description += service_message
                affected_releases = self.get_known_affected_releases(message=message)
                if affected_releases:
                    for x in affected_releases:
                        known_affected_releases.add(x)

            # issue passed all filters - format bug entry
            bug_entry = {
                "bugId": issue["Id"],
                "bugUrl": f"https://admin.microsoft.com/adminportal/home?#/windowsreleasehealth/:/alerts/{issue['Id']}",
                "description": description,
                "priority": "Unspecified",
                "snCiFilter": f"{affected_ci_query_base}osLIKE{managed_product.name}",
                "snCiTable": "cmdb_ci_computer",
                "summary": issue['IssueTitle'],
                "status": issue_status.title(),
                "knownAffectedReleases": ", ".join(sorted(list(known_affected_releases))),
                "vendorData": {},
                "vendorCreatedDate": self.timestamp_format(issue['KbReleaseDate']),
                "vendorLastUpdatedDate": self.timestamp_format(issue['LastUpdated']),
                "processed": 0,
                "managedProductId": managed_product.id,
                "vendorId": self.vendor_id,
            }
            bugs.append(bug_entry)
        return bugs

    @staticmethod
    def get_known_affected_releases(message):
        """
        parse out affected releases from service message updates
        :return:
        """
        releases = set()
        releases_container = re.findall(r"(?<=Server:).*?(?=\n)", message['MessageText'])
        if releases_container:
            for r in releases_container[0].split(";"):
                releases.add(r.strip())
        return releases

    def get_access_bug_kbs(self):
        """
        1. parse kb links from an html dedicated to Access issue kbs
        2. filter out links missing 'access' in the description
        :return:
        """
        self.logger.info("'Microsoft Access' - getting bug KBs")
        url = "https://support.microsoft.com/en-us/office/fixes-or-workarounds-for-recent-issues-in-access-" \
              "54962069-14f4-4474-823a-ff7e5974a570"
        response = download_instance(link=url, session=False)
        if not response:
            self.logger.error(f"vendor connection error - {url}")
            raise VendorConnectionError(
                url=url, internal_message="vendor connection error",
                event_message="a connection to the vendor could not be established - we are actively working on a "
                              "fix"
            )
        root = lxml.html.fromstring(response.text)
        kb_urls = root.xpath("//section[@class='ocpSection']//ul//a[contains(@class, 'ocpArticleLink')]")
        if not kb_urls:
            self.logger.error(f"vendor connection error - {url}")
            raise VendorResponseError(
                url=url, internal_message="vendor response error - missing bug urls",
                event_message="vendor data could not be retrieved - we are actively working on a "
                              "fix"
            )
        self.logger.info(f"'Microsoft Access' - {len(kb_urls)} KBs found | crawling KB pages")
        kbs = []
        for kb in kb_urls:
            summary = kb.xpath("text()")[0]
            url = f"https://support.microsoft.com{kb.xpath('@href')[0]}"

            bug_entry = {
                "priority": "Unspecified",
                "status": "Fixed",
                "bugId": "",
                "vendorId": self.vendor_id,
                "bugUrl": url,
                "knownAffectedOs": "Microsoft Windows",
                "vendorData": {},
                "ciSysIds": "",
                "managedProductId": "",
                "hasKb": True,
                "summary": summary,
                "description": ""
            }

            # bug has a kb - crawl html and enrich the bug entry
            kbs.append(bug_entry)
        self.bug_kbs_crawling_manager(bugs=kbs, product_name='Microsoft Access')
        return self.kb_bugs

    def get_aws_secret_value(self, secret_name, mandatory_fields):
        """
        - retrieve secret value from AWS Secrets Manager
        :param secret_name:
        :param mandatory_fields:
        :return:
        """
        try:
            get_secret_value_response = self.secret_manager_client.get_secret_value(
                SecretId=secret_name
            )
            if "SecretString" in get_secret_value_response:
                secret = json.loads(get_secret_value_response["SecretString"])
                for field in mandatory_fields:
                    if not secret.get(field):
                        raise ValueError(f"AWS secret error - missing mandatory field '{field}'", "SecretManager")
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

    def process_login_step(self, step_count, step, step_id, stored_data, session):
        """

        :param step:
        :param step_id:
        :param stored_data:
        :param step_count:
        :param session:
        :return:
        """
        self.logger.info(f"'{self.vendor_id}' - admin dashboard auth step {step_id}/{step_count} | "
                         f"{step['log_message']}")
        if step["post"]:
            post_form = step['form']
            for field in step['form_fields_map']:
                post_form[field] = stored_data[field]
            if step["json_form"]:
                response = download_instance(link=step["url"], session=session, method="POST", json=post_form)
            else:
                response = download_instance(link=step["url"], session=session, method="POST", payload=post_form)

        else:
            response = download_instance(link=step["url"], session=session)

        if not response:
            message = f"'{self.vendor_id}' API connection error - authentication failed | {step['url']}"
            self.logger.error(message)
            raise ApiConnectionError(
                url=step['url'], internal_message=message,
                event_message="vendor API connection error - we are actively wokring on a fix"
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
        if step["parse_html"]:
            root = lxml.html.fromstring(response.text)
            for path in list(step["xpaths"]):
                value = root.xpath(path["xpath"])
                stored_data[path["title"]] = value
        return stored_data, session

    def gen_admin_dashboard_tokens(self, username, password):
        """
        generate auth tokens for the msft admin dashboard
        :param username:
        :param password:
        :return:
        """
        credentials_form = {
            "username": username, "isOtherIdpSupported": True, "checkPhones": False, "isRemoteNGCSupported": True,
            "isCookieBannerShown": False, "isFidoSupported": True, "originalRequest": "", "country": "US",
            "forceotclogin": False, "isExternalFederationDisallowed": False, "isRemoteConnectSupported": False,
            "federationFlags": 0, "isSignup": False, "flowToken": "", "isAccessPassSupported": True
        }
        login_form = {
            "i13": "0", "login": username, "loginfmt": username, "type": "11", "LoginOptions": "3", "lrt": "",
            "lrtPartition": "", "hisRegion": "", "hisScaleUnit": "", "passwd": password, "ps": "2",
            "psRNGCDefaultType": "", "psRNGCEntropy": "", "psRNGCSLK": "", "canary": "", "ctx": "", "hpgrequestid": "",
            "flowToken": "", "PPSX": "", "NewUser": "1", "FoundMSAs": "", "fspost": "0", "i21": "0",
            "CookieDisclosure": "0", "IsFidoSupported": "1", "isSignupPost": "0", "i2": "1", "i17": "", "i18": "",
            "i19": "81076"
        }
        kmsi_form = {
            "LoginOptions": "3", "type": "28", "ctx": "", "hpgrequestid": "", "flowToken": "", "canary": "", "i2": "",
            "i17": "", "i18": "", "i19": "1060492"
        }
        landing_form = {
            "code": "", "id_token": "", "state": "", "session_state": "", "correlation_id": ""
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
                "parse_html": False, 'xpaths': []
            },
        ]
        session = requests.session()
        stored_data = {}
        for i, step in enumerate(steps, 1):
            stored_data, session = self.process_login_step(
                step_id=i, step=step, step_count=len(steps), stored_data=stored_data, session=session
            )

        cookies = session.cookies.get_dict()
        try:
            tokens = {
                "RootAuthToken": cookies['RootAuthToken'],
                'OIDCAuthCookie': cookies["OIDCAuthCookie"],
                'UserIndex': cookies['UserIndex']
            }
        except KeyError as e:
            internal_message = f"'{self.vendor_id}' - invalid credentials"
            event_message = f"'{self.vendor_id}' API response error - login failed | go to the vendor configuration " \
                            f"page and verify the credentials"
            raise ApiResponseError(
                internal_message=internal_message, event_message=event_message,
                url="https://admin.microsoft.com/landing"
            ) from e

        return tokens

    @staticmethod
    def format_sql_bugs(bugs, sn_ci_table):
        """
        pre-db insert format
        1. add snCiFilter based on CI sysIds
        2. add snCiTable
        3. remove unnecessary fields
        :param bugs:
        :param sn_ci_table:
        :return:
        """
        for bug in bugs:
            bug['snCiFilter'] = f"sys_idIN{','.join(bug['ciSysIds'])}"
            bug['snCiTable'] = sn_ci_table
            bug['description'] = bug['description'].strip()
            del bug['releaseUrl']
            del bug['hasKb']
            del bug['ciSysIds']
            try:
                del bug['knownAffectedItems']
            except KeyError:
                pass
        return bugs

    @staticmethod
    def format_access_bugs(bugs, active_cis):
        """
        pre-db insert format
        1. add snCiFilter based on CI sysIds and Known Affected Items
        2. add managedProduct ID
        2. remove unnecessary fields
        :param bugs:
        :param active_cis:
        :return:
        """
        formatted_bugs = []
        for bug in bugs:
            # a ci is affected if the correlating product version and the kw 'access' are found in one or more items
            # in bug['knownAffectedItems'] and managed_product_last_execution for the ci is is older than
            # bug['vendorLastUpdatedDate'] ( - 2 days )
            # the ci is also affected if the general 'Access for Microsoft 365' is included in knownAffectedItems
            affected_cis = [
                x['sys_id'] for x in active_cis if [
                    y for y in bug['knownAffectedItems'] if x['version_name'] in y and "access" in y.lower() or
                    "microsoft 365" in y.lower() and "access" in y.lower()
                ]
                and bug['vendorLastUpdatedDate'] >= (x['managed_product_last_execution'] - datetime.timedelta(days=2))
            ]

            affected_managed_products = [
                x['managed_product'].id for x in active_cis if [
                    y for y in bug['knownAffectedItems'] if x['version_name'] in y and "access" in y.lower() or
                    "microsoft 365" in y.lower() and "access" in y.lower()
                ]
                and bug['vendorLastUpdatedDate'] >= (x['managed_product_last_execution'] - datetime.timedelta(days=2))
            ]

            if not affected_cis:
                continue

            # the CIs share the same sn_ci_table
            managed_product_id = affected_managed_products[0]

            bug['snCiFilter'] = f"sys_idIN{','.join(affected_cis)}"
            bug['snCiTable'] = active_cis[0]['sn_ci_table']
            bug['description'] = bug['description'].strip()
            bug['managedProductId'] = managed_product_id
            del bug['knownAffectedItems']
            del bug['hasKb']
            del bug['ciSysIds']
            formatted_bugs.append(bug)
        return formatted_bugs

    def get_windows_issues(self, days_back, tokens):
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
        url = f"https://admin.microsoft.com/admin/api/windowsreleasehealth/status/all?historyDays={days_back}"
        self.logger.info(
            f"'{self.vendor_id}' - getting windows health issues | days back: {days_back}"
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
            if not services['VersionsKnownIssues']:
                internal_error = f"'{self.vendor_id}' - vendor API response empty error | {url}"
                event_message = f"vendor API response error - we are actively working on fix"
                self.logger.error(internal_error)
                raise ApiResponseError(
                    url=url, internal_message=internal_error,
                    event_message=event_message
                )
            return services['VersionsKnownIssues']
        except json.JSONDecodeError as e:
            internal_message = f"'{self.vendor_id}' - API response error | failed to generate auth tokens"
            event_message = f"{self.vendor_id} - API connection error, we are actively working on a fix"
            self.logger.error(internal_message)
            raise ApiResponseError(
                url=url, internal_message=internal_message, event_message=event_message
            ) from e
