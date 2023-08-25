"""
created 2022-02-10
"""
import csv
import datetime
import json
import logging.config
import math
import sys
import threading
import urllib.parse
from queue import Queue
from time import sleep

import requests
from requests.packages import urllib3

urllib3.disable_warnings()


logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class CiscoSecurityAdvisoryClass:
    """
    1. retrieve security advisories from https://tools.cisco.com/security/center/publicationListing.x
    2. filter by published date based on days_back
    3. look for NVD cve data using the advisories cve id
    4. calculate published timestamps comparing vendor and NVD
    5. generate a csv output file
    """
    def __init__(self, nvd_api_key, days_back=365, num_threads=1):
        """
        load instance
        :param days_back:
        :param nvd_api_key:
        """
        self.vendor_id = 'cisco'
        self.num_threads = int(num_threads)
        self.days_back = days_back
        self.nvd_api_key = nvd_api_key
        self.utc_now = datetime.datetime.utcnow()
        self.first_published_start_date = (
                datetime.datetime.utcnow() - datetime.timedelta(days=int(days_back))
        ).strftime("%Y/%m/%d")
        self.logger = logger
        self.nvd_processed_security_advisories = dict()
        self.nvd_requests_made = 0
        self.security_advisories_found = 0
        self.output_file = ""

    def download_instance(self, link, headers, method='GET', retry=10, timeout=20):
        """
        simple http downloader
        :param link:
        :param retry:
        :param method:
        :param timeout:
        :param headers
        :return:
            """
        tries = 0
        last_response = ""
        while tries < retry:
            try:
                request = requests.request(method=method, url=link, timeout=timeout, headers=headers)
                last_response = request
                if request.status_code == 404:
                    if "Request forbidden by administrative rules." in request.text:
                        sleep(2)
                        tries += 1
                        continue
                    return request

                if request.status_code in [401, 403]:
                    self.logger.error(
                        "{}: Download failed with status code {} - {}".format(
                            request.url, request.status_code, request.text
                        )
                    )
                    tries += 1
                    continue

                if request.status_code != 200:
                    self.logger.error(
                        "{}: Download failed with status code {}".format(
                            request.url, request.status_code
                        )
                    )
                    tries += 1
                    continue

                return request

            except requests.exceptions.ReadTimeout:
                tries += 1
                continue
            except requests.exceptions.ConnectTimeout:
                tries += 1
                continue
            except requests.exceptions.ConnectionError:
                tries += 1
                continue

        self.logger.error(f"{link}: Download failed with with max retires")
        return last_response

    def csv_writer(self, entries, fieldnames):
        """
        write results to csv file
        :param entries:
        :param fieldnames:
        :return:
        """
        output_file = f'{self.vendor_id}-nvd-publish-stats-{datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")}.csv'
        self.output_file = output_file
        with open(self.output_file, 'a') as outputs:
            writer = csv.DictWriter(outputs, fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(entries)

    def get_cve_entry(self, q):
        """
        get cve entry from NVD
        :return:
        """
        def process(security_advisory):
            """

            :return:
            """
            security_advisory['impactPublished'] = False
            security_advisory['cvePublished'] = False
            security_advisory["nvdPublished"] = False
            security_advisory['firstPublishedSort'] = self.timestamp_format(security_advisory['firstPublished'])
            self.nvd_requests_made += 1
            if not security_advisory.get('cve'):
                security_advisory['cve'] = ""
                # convert timestamps to a compatible excel strings
                security_advisory['firstPublished'] = self.timestamp_format(security_advisory['firstPublished'])
                security_advisory['lastPublished'] = self.timestamp_format(security_advisory['lastPublished'])
                security_advisory['firstPublished'] = security_advisory['firstPublished'].strftime(
                    '%Y-%m-%d %H:%M:%S'
                )
                security_advisory['lastPublished'] = security_advisory['lastPublished'].strftime(
                    '%Y-%m-%d %H:%M:%S'
                )
            else:
                request_cve = security_advisory['cve'].split(",")[0]
                security_advisory['cvePublished'] = True
                nvd_api_url = f"https://services.nvd.nist.gov/rest/json/cve/1.0/{request_cve}?apiKey={self.nvd_api_key}"
                security_advisory['nvdCveApiUrl'] = nvd_api_url
                security_advisory['nvdCveUrl'] = f"https://nvd.nist.gov/vuln/detail/{request_cve}"
                security_advisory['mitreCveUrl'] = f"https://cve.mitre.org/cgi-bin/cvename.cgi?name={request_cve}"
                response = self.download_instance(link=nvd_api_url, headers="")
                if response.status_code not in [404, 200]:
                    security_advisory["nvdPublished"] = 'unable to verify'
                data = {}
                try:
                    data = json.loads(response.text)
                except json.JSONDecodeError:
                    security_advisory["nvdPublished"] = 'unable to verify'
                if data:
                    error_message = data.get('message') or ""
                    if 'unable to find' in error_message.lower():
                        security_advisory["nvdPublished"] = False
                    else:
                        nvd_entry = data['result']['CVE_Items'][0]
                        security_advisory['nvdPublished'] = True
                        security_advisory['nvdPublishedDate'] = nvd_entry['publishedDate']
                        security_advisory['nvdUpdatedDate'] = nvd_entry['lastModifiedDate']
                        security_advisory['nvdCveAssigner'] = nvd_entry['cve']['CVE_data_meta']['ASSIGNER']

                        # convert timestamps to objects
                        security_advisory['firstPublished'] = self.timestamp_format(security_advisory['firstPublished'])
                        security_advisory['lastPublished'] = self.timestamp_format(security_advisory['lastPublished'])
                        security_advisory['nvdPublishedDate'] = self.timestamp_format(
                            security_advisory['nvdPublishedDate']
                        )
                        security_advisory['nvdUpdatedDate'] = self.timestamp_format(security_advisory['nvdUpdatedDate'])

                        # generate time deltas in hours
                        security_advisory['publishedDelta'] = self.gen_timestamps_delta(
                            timestamp_a_object=security_advisory['firstPublished'],
                            timestamp_b_object=security_advisory['nvdPublishedDate']
                        )
                        security_advisory['updatedDelta'] = self.gen_timestamps_delta(
                            timestamp_a_object=security_advisory['lastPublished'],
                            timestamp_b_object=security_advisory['nvdUpdatedDate']
                        )

                        # convert timestamps to a compatible excel strings
                        security_advisory['firstPublished'] = security_advisory['firstPublished'].strftime(
                            '%Y-%m-%d %H:%M:%S'
                        )
                        security_advisory['lastPublished'] = security_advisory['lastPublished'].strftime(
                            '%Y-%m-%d %H:%M:%S'
                        )
                        security_advisory['nvdPublishedDate'] = security_advisory['nvdPublishedDate'].strftime(
                            '%Y-%m-%d %H:%M:%S'
                        )
                        security_advisory['nvdUpdatedDate'] = security_advisory['nvdUpdatedDate'].strftime(
                            '%Y-%m-%d %H:%M:%S'
                        )

                        security_advisory['nvd_cve_base_severity'] = ""
                        security_advisory['nvd_cve_base_exploitability'] = ""
                        security_advisory['nvd_cve_base_impact'] = ""
                        security_advisory['nvd_cve_cvssV2_base_score'] = ""
                        security_advisory['nvd_cve_cvssV2_access_vector'] = ""
                        security_advisory['nvd_cve_cvssV2_access_complexity'] = ""
                        security_advisory['nvd_cve_cvssV2_authentication'] = ""
                        security_advisory['nvd_cve_cvssV2_confidentiality_impact'] = ""
                        security_advisory['nvd_cve_cvssV2_integrity_impact'] = ""
                        security_advisory['nvd_cve_cvssV2_availability_impact'] = ""
                        if nvd_entry.get('impact'):
                            security_advisory['impactPublished'] = True
                            base_impact = nvd_entry['impact']['baseMetricV2']
                            cvss_impact = nvd_entry['impact']['baseMetricV2']['cvssV2']
                            security_advisory['nvd_cve_base_severity'] = base_impact['severity']
                            security_advisory['nvd_cve_base_exploitability'] = base_impact['exploitabilityScore']
                            security_advisory['nvd_cve_base_impact'] = base_impact['impactScore']
                            security_advisory['nvd_cve_cvssV2_base_score'] = cvss_impact['baseScore']
                            security_advisory['nvd_cve_cvssV2_access_vector'] = cvss_impact['accessVector']
                            security_advisory['nvd_cve_cvssV2_access_complexity'] = cvss_impact['accessComplexity']
                            security_advisory['nvd_cve_cvssV2_authentication'] = cvss_impact['authentication']
                            security_advisory['nvd_cve_cvssV2_confidentiality_impact'] = \
                                cvss_impact['confidentialityImpact']
                            security_advisory['nvd_cve_cvssV2_integrity_impact'] = cvss_impact['integrityImpact']
                            security_advisory['nvd_cve_cvssV2_availability_impact'] = cvss_impact['availabilityImpact']

            self.nvd_processed_security_advisories[security_advisory['identifier']] = security_advisory
            if self.nvd_requests_made % 10 == 0:
                self.logger.info(
                    f"'{self.vendor_id}' - {self.nvd_requests_made}/{self.security_advisories_found} "
                    f"cve entries processed"
                )

        while not q.empty():
            queue = q.get()
            process(security_advisory=queue)
            q.task_done()

    def get_nvd_cve_data(self, security_advisories):
        """
        multi-processing manager to retrieve data from NVD
        :param security_advisories:
        :return:
        """
        q = Queue()

        for entry in security_advisories:
            q.put(entry)

        for _ in range(self.num_threads):
            t = threading.Thread(target=self.get_cve_entry, args=(q,))
            t.start()

        q.join()
        self.logger.info(
            f"'{self.vendor_id}' - {self.nvd_requests_made}/{self.security_advisories_found} "
            f"cve entries processed"
        )
        return list(self.nvd_processed_security_advisories.values())

    def get_cisco_security_advisories(self):
        """
        get security advisories from cisco based on date range, paginate if necessary
        :return:
        """
        first_published_escape = urllib.parse.quote_plus(self.first_published_start_date)
        total_pages = 1
        page_no = 0
        entries = []
        dedup = set()
        try:
            while page_no < total_pages:
                offset = page_no * 100
                page_no += 1
                self.logger.info(
                    f"'{self.vendor_id}' - getting security advisories page {page_no} | first published date: "
                    f"{self.first_published_start_date}"
                )
                request_url = self.gen_api_url(first_published_start_date=first_published_escape, offset=offset)
                response = self.download_instance(link=request_url, headers="")
                results = json.loads(response.text)
                total_pages = math.ceil(results[0]['totalCount'] / 100)
                for x in results:
                    dedup.add(x['identifier'])
                entries.extend(results)
                continue
        except json.JSONDecodeError as e:
            print(e)
        return entries

    @staticmethod
    def gen_api_url(
            offset, cisco_bug_ids="", cve_ids="", cve_base_score_min="", first_published_end_date="", keyword="",
            first_published_start_date="", last_published_end_date="", last_published_start_date="", publication_id="",
            severity='', cisco_resource_id=''
    ):
        """
        generate api request url based on selected filters
        * all the params are optional

        :param offset: 100
        :param cisco_bug_ids: optional - "CSCvz88279,CSCvz34380"
        :param cve_ids: optional - "CVE-2022-20680,CVE-2022-20685"
        :param publication_id: optional - "cisco-sa-swg-fbyps-3z4qT7p"
        :param cisco_resource_id: optional - "213561" ( Cisco Nexus 3000 Series Switch )
               for more info - https://tools.cisco.com/security/center/productBoxData.x?prodType=CISCO
        :param severity: optional - choose from ['critical', 'high', 'medium', 'low', 'informational']
        :param cve_base_score_min: optional - 0 > float > 10
        :param keyword: optional - "Cisco NX-OS"
        :param first_published_start_date: optional - "2022/02/10"
        :param first_published_end_date: optional - "2022/02/10"
        :param last_published_start_date: optional - "2022/02/10"
        :param last_published_end_date: optional - "2022/02/10"

        :return:
        """
        base_url = "https://tools.cisco.com/security/center/publicationService.x" \
                   f"?ciscoBugs={cisco_bug_ids}" \
                   f"&criteria={'exact' if keyword else ''}" \
                   f"&cves={cve_ids}" \
                   f"&cvssBaseScoreMin={cve_base_score_min}" \
                   f"&cwe=" \
                   f"&firstPublishedEndDate={first_published_end_date}" \
                   f"&firstPublishedStartDate={first_published_start_date}" \
                   f"&identifiers={publication_id}" \
                   f"&keyword={keyword}" \
                   f"&lastPublishedEndDate={last_published_end_date}" \
                   f"&lastPublishedStartDate={last_published_start_date}" \
                   f"&last_published_date=" \
                   f"&securityImpactRatings={severity}" \
                   f"&resourceIDs={cisco_resource_id}" \
                   "&sort=-last_published" \
                   "&title=" \
                   "&limit=100" \
                   f"&offset={offset}" \
                   "&publicationTypeIDs=1"
        return base_url

    @staticmethod
    def gen_timestamps_delta(timestamp_a_object, timestamp_b_object):
        """
        get the delta of two datetime objects
        :param timestamp_a_object:
        :param timestamp_b_object:
        :return:
        """
        return (timestamp_b_object - timestamp_a_object).total_seconds() / 3600

    @staticmethod
    def timestamp_format(time_str):
        """
        convert timedate strings to timedate objects
        :param time_str:
        :return:
        """
        # max 6 digit micro second
        known_formats = [
            "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%MZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"
        ]
        fmt_time = ""
        for _i, fmt in enumerate(known_formats):
            check_string = time_str[:19]
            try:
                fmt_time = datetime.datetime.strptime(check_string, fmt)
                break
            except ValueError:
                continue
        if fmt_time:
            return fmt_time
        return time_str

    def start(self):
        """
        1. get security advisories from cisco
        2. get NVD CVE data for the security advisories
        3. calc delta for NVD and VENDOR published dates
        4. generate a CSV output file
        :return:
        """
        security_advisories = self.get_cisco_security_advisories()
        self.security_advisories_found = len(security_advisories)
        self.logger.info(f"'{self.vendor_id}' - {self.security_advisories_found} security advisories found")
        security_advisories_w_nvd_fields = self.get_nvd_cve_data(security_advisories=security_advisories)
        output_fieldnames = [
            "identifier", 'cve', "title", 'severity', 'cvePublished', 'nvdPublished', 'firstPublished', 'lastPublished',
            'nvdPublishedDate', 'nvdUpdatedDate', 'publishedDelta', 'updatedDelta', 'url', 'nvdCveApiUrl', 'nvdCveUrl',
            'mitreCveUrl', 'status', 'ciscoBugId', 'cwe', 'summary', 'workarounds', 'impactPublished',
            'nvd_cve_base_severity', 'nvd_cve_base_exploitability', 'nvd_cve_base_impact', 'nvd_cve_cvssV2_base_score',
            'nvd_cve_cvssV2_access_vector', 'nvd_cve_cvssV2_access_complexity', 'nvd_cve_cvssV2_authentication',
            'nvd_cve_cvssV2_confidentiality_impact', 'nvd_cve_cvssV2_integrity_impact',
            'nvd_cve_cvssV2_availability_impact',
        ]
        # sort by firstPublishedSort
        security_advisories_w_nvd_fields = sorted(
            security_advisories_w_nvd_fields, key=lambda x: x['firstPublishedSort'], reverse=True
        )
        self.csv_writer(entries=security_advisories_w_nvd_fields, fieldnames=output_fieldnames)


# ---------------------------------------------------------------------------------------------------------------------#
#                                                  USER INPUTS                                                         #
# ---------------------------------------------------------------------------------------------------------------------#
# use hardcoded NVD api key if user does not provide one
nvd_api_access_key = input("provide an NVD api key ( leave empty if not available ): ").strip()
if not nvd_api_access_key:
    nvd_api_access_key = "36cdf4f4-e501-4fc7-8d82-b81b9a2f6f37"

# mandatory advisories_days_back integer
advisories_days_back = 0
while True:
    try:
        advisories_days_back = input("advisories days back: ")
        int(advisories_days_back)
        break
    except ValueError:
        continue

# mandatory advisories_days_back integer
threads_count = 0
while True:
    try:
        threads_count = input("threads count ( press enter for default ): ")
        if threads_count:
            int(threads_count)
            break
    except ValueError:
        continue
if threads_count:
    instance = CiscoSecurityAdvisoryClass(
        nvd_api_key=nvd_api_access_key, days_back=advisories_days_back, num_threads=threads_count
    )
else:
    instance = CiscoSecurityAdvisoryClass(
        nvd_api_key=nvd_api_access_key, days_back=advisories_days_back
    )
instance.start()
print(f"\nresults saved: {instance.output_file}\n")
input("press any key to terminate\n")
