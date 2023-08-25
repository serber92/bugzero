#!/usr/bin/env python3
"""
updated 2021-06-28
- switch from DynamoDB to Aurora MySQL DB

updated 2021-08-28
- added bug_zero_vendor_status_update(func) to update service/serviceExecution entries
"""

import datetime
import json
import logging.config
import math
import re
import sys

import lxml.html
import requests
from requests.packages import urllib3

from download_manager import download_instance

urllib3.disable_warnings()

logger = logging.getLogger()


class HpeApiClient:
    """
    - a class with methods to consume Hpe's public API, work with Aurora Serverless MySQL tables
      strings
    - errors are logged and reported as service now events
    """

    def __init__(
        self,
        vendor_id,
    ):
        """"""
        self.logger = logger

        # ------------------------------------------------------------------------------------------------------------ #
        #                                         GLOBAL VARIABLES                                                     #
        # ------------------------------------------------------------------------------------------------------------ #
        self.bug_ids = set()
        self.dedup_count = 0
        self.drivers = dict()
        self.earliest_execution = datetime.datetime.now()
        self.hpe_auth = ""
        self.logger = logger
        self.resource_descriptions = {
            'product_search': {
                "resource_description": "Coveo_Search_Product_Source_Name__c", "resource_name": ""
            },
            'bugs_search': {
                "resource_description": "Coveo_Search_KMDB_Document_Source_Name__c", "resource_name": ""
            },
            'organization_id': {
                "resource_description": "Coveo_Organization_Id__c", "resource_name": ""
            },
            'software_search': {
                "resource_description": "Coveo_Search_Software_Source_Name__c", "resource_name": ""
            }
        }
        self.vendor_id = vendor_id

    def get_api_data_resource_names(self):
        """
        retrieve the latest resource name for the resource_description, required for making api requests
        :return:
        """
        self.logger.info(f"retrieving the current resource names - {json.dumps(self.resource_descriptions)}")
        # unix timestamp
        timestamp = math.floor(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)
        resources_url = f"https://support.hpe.com/connect/resource/{timestamp}/DCESearchProperties"
        response = download_instance(link=resources_url, headers=None)
        resources_json = json.loads(response.text)[0]
        for v in self.resource_descriptions.values():
            resource_description = v["resource_description"]
            resource_name = resources_json[resource_description]
            v["resource_name"] = resource_name
            self.logger.info(f"'{resource_description}' - retrieved resource name: {resource_name}")

    def get_all_related_product_oids(self, vendor_product_id, oid_type, tab):
        """
        retrieve all the related product oids to be used in the get bugs query
        :param vendor_product_id: a unique hpe product identifier
        :param oid_type
        :param tab
        :return:
        """
        headers = {
            "Authorization": self.hpe_auth,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        api_url = f"https://platform.cloud.coveo.com/rest/search/v2?organizationId=" \
                  f"{self.resource_descriptions['organization_id']['resource_name']}"
        form = {
            "aq": f'@source=="{self.resource_descriptions[oid_type]["resource_name"]}"',
            "q": vendor_product_id,
            "searchHub": 'HPE-Product-Page',
            "tab": tab
        }
        try:
            response = download_instance(link=api_url, method="POST", post_form=form, headers=headers)
            results = json.loads(response.text)

            if response.status_code != 200:
                raise ConnectionError
        except (
                TimeoutError, ConnectionError, ConnectionRefusedError, ConnectionAbortedError, json.JSONDecodeError
        ) as e:
            (
                exception_type,
                _exception_object,
                exception_traceback,
            ) = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            error = {
                "url": api_url,
                "errorType": str(exception_type),
                "errorMsg": str(e),
                "source": "",
                "service": f"{str(filename)} - line {line_number}",
            }
            self.logger.error(f"API connection error - {json.dumps(error)}")
            raise ConnectionError("Vendor integration error - HPE data APIs are not available") from e

        if not results['totalCount']:
            self.logger.error(f"cant find related productOIDs - {results}")
            raise ConnectionError("Vendor integration error - HPE data APIs are not available")
        # target_oids = set(results['results'][0]["raw"]['kmpmlevel7oidlist'].split(","))
        # target_oids.add(results['results'][0]["raw"]['kmpmlevel5oid'])
        # target_oids.add(str(vendor_product_id))
        return results['results'][0]["raw"]['kmpmlevel5oid']

    def get_bugs_by_product_oid(
        self,
        managed_product_id,
        managed_product_name,
        target_oids,
        product_priorities,
        earliest_bug_date,
    ):
        """
        retrieve all bugs for target_oids
        :param target_oids: unique hpe product oids
        :param managed_product_id: bugZero managedProductId
        :param managed_product_name: bugZero managedProduct name
        :param product_priorities: bug priority codes
        :param earliest_bug_date: earliest date for filtering out bugs
        :return:
        """
        results = []
        headers = {
            "Authorization": f"{self.hpe_auth}",
            "Accept": "application/json",
        }
        api_url = f"https://platform.cloud.coveo.com/rest/search/v2?organizationId=" \
                  f"{self.resource_descriptions['organization_id']['resource_name']}"
        payload = {
            "isGuestUser": False,
            "cq": f'@source=="{self.resource_descriptions["bugs_search"]["resource_name"]}"',
            "searchHub": "HPE-Product-Page",
            "tab": "Documents",
            "locale": "en",
            "firstResult": "0",
            "numberOfResults": "250",
            "excerptLength": "150",
            "enableDidYouMean": True,
            "sortCriteria": "relevancy",
            "queryFunctions": [],
            "rankingFunctions": [],
            "facets": [
                {"facetId": "@kmdoctypedetails", "field": "kmdoctypedetails", "type": "specific",
                 "injectionDepth": 1000,
                 "filterFacetCount": True, "currentValues": [
                    {"value": "cv66000022", "state": "selected"},
                    {"value": "cv66000024", "state": "selected"},
                    {"value": "cv66000027", "state": "selected"}
                    ],
                 "numberOfValues": 15, "freezeCurrentValues": True, "preventAutoSelect": True, "isFieldExpanded": True},
                {"facetId": "@kmdoclanguagecode", "field": "kmdoclanguagecode", "type": "specific",
                 "injectionDepth": 1000, "filterFacetCount": True, "currentValues": [
                    {"value": "cv1871440", "state": "selected"}
                    ],
                 "numberOfValues": 8, "freezeCurrentValues": False, "preventAutoSelect": True, "isFieldExpanded": True},
            ],
            "facetOptions": {},
            "categoryFacets": [],
            "retrieveFirstSentences": "true",
            "timezone": "America/New_York",
            "enableQuerySyntax": "false",
            "enableDuplicateFiltering": "true",
            "enableCollaborativeRating": "false",
            "debug": 'true',
            "context": {"tracking_id": "HPESCYIL2@SEr-yme9z9WYG-algAAAC0",
                        "active_features": "DCS,DHFWS,SA2,cep2_active,cep2_eligible,cep2_hpe_org,enablePatchStorage,"
                                           "sa2_software_indexer_v2_toggle,sa2_ui_enable_token_client_caching,"
                                           "toggleCsr",
                        "productName": managed_product_name, "targetOids": target_oids},
            "allowQueriesWithoutKeywords": "true"
        }
        page = 1
        paginate = True
        try:
            while paginate:
                self.logger.info(f"{managed_product_name} - getting bugs page {page} - {json.dumps(payload)}")
                request = requests.post(url=api_url, headers=headers, json=payload)
                if request.status_code != 200:
                    raise ConnectionError
                items = json.loads(request.text)
                results.extend(items["results"])
                first_results = int(payload["firstResult"])
                if int(payload["firstResult"]) < (items['totalCountFiltered'] - int(payload["numberOfResults"])):
                    page += 1
                    first_results += int(payload["numberOfResults"])
                    payload["firstResult"] = str(first_results)
                    continue
                paginate = False
        except (
                TimeoutError, ConnectionError, ConnectionRefusedError, ConnectionAbortedError, json.JSONDecodeError
        ) as e:
            (
                exception_type,
                _exception_object,
                exception_traceback,
            ) = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            error = {
                "url": api_url,
                "errorType": str(exception_type),
                "errorMsg": str(e),
                "source": "",
                "service": f"{str(filename)} - line {line_number}",
            }
            self.logger.error(f"API connection error - {json.dumps(error)}")
            raise ConnectionError("Vendor integration error - HPE data APIs are not available") from e

        # iterate bugs
        filtered_bugs = list()
        for document in results:
            if document['raw']['kmdocid'] in self.bug_ids:
                self.dedup_count += 1
            self.bug_ids.add(document['raw']['kmdocid'])

            bug_data = dict()

            bug_data["vendorCreatedDate"] = self.timestamp_format(document["raw"]["kmdoccontentdate"])
            bug_data["vendorLastUpdatedDate"] = datetime.datetime.strptime(
                document["raw"]["kmdoclastmod"][:10], "%m/%d/%Y"
            )

            # 1. filter bugs ( +2 days ) older than the lastExecution date
            if (bug_data["vendorLastUpdatedDate"] + datetime.timedelta(days=2)) <= earliest_bug_date:
                continue

            # 2. filter bugs based on severity levels
            priority = product_priorities.get(document["raw"]["kmdoctypedetails"], None)
            if not priority:
                continue

            bug_data["bugId"] = document['raw']['kmdocid']
            bug_data["bugUrl"] = f"https://support.hpe.com/hpesc/public/docDisplay?docLocale=en_US&docId=" \
                                 f"{document['raw']['kmdocid']}"

            html_data = self.get_document_details(doc_id=document['raw']['kmdocid'])
            bug_data["description"] = f"Description: {html_data['description']}\n " \
                                      f"Resolution:  {html_data['resolution']}\n" \
                                      f"Scope:  {html_data['scope']}\n" \
                                      f"Affected Hardware:  {html_data['affected_hardware']}\n" \
                                      f"Affected Software:  {html_data['affected_software']}\n" \
                                      f"Affected Operating System:  {html_data['affected_operating_system']}"
            bug_data["knownAffectedHardware"] = html_data['affected_hardware'].replace('Not Applicable', '')
            bug_data["knownAffectedReleases"] = html_data['affected_software'].replace('Not Applicable', '')
            bug_data["knownAffectedOs"] = html_data['affected_operating_system'].replace('Not Applicable', '')
            bug_data["managedProductId"] = managed_product_id
            # convert sbPriority value to label
            bug_data["priority"] = priority
            bug_data["processed"] = 0
            bug_data["snCiTable"] = ""
            bug_data["snCiFilter"] = ""
            bug_data["summary"] = document["raw"]["kmdocfulltitle"]

            bug_data["vendorId"] = self.vendor_id
            bug_data["vendorData"] = {
                "bugProductNames":
                    document["raw"]["kmdoctargetproductl1l5namelist"] if 'kmdoctargetproductl1l5namelist' in
                                                                         document["raw"] else "",
                "bugProductIds": document["raw"]["kmdoctargetoidlist"],
                "bugConcepts": document["raw"]["concepts"],
            }
            filtered_bugs.append(bug_data)

        return filtered_bugs

    def get_software_by_product_oid(
            self,
            managed_product_id,
            managed_product_name,
            target_oids,
            product_priorities,
            earliest_bug_date,
    ):
        """
        retrieve related drivers and software for target_oids
        :param target_oids: unique hpe product oids
        :param managed_product_id: bugZero managedProductId
        :param managed_product_name: bugZero managedProduct name
        :param product_priorities: bug priority codes
        :param earliest_bug_date: earliest date for filtering out bugs
        :return:
        """
        results = []
        headers = {
            "Authorization": f"{self.hpe_auth}",
            "Accept": "application/json",
        }
        api_url = f"https://platform.cloud.coveo.com/rest/search/v2?organizationId=" \
                  f"{self.resource_descriptions['organization_id']['resource_name']}"
        payload = {
            "isGuestUser": False,
            "cq": f'@source=="{self.resource_descriptions["software_search"]["resource_name"]}"',
            "searchHub": "HPE-Product-Page",
            "tab": "DriversandSoftware",
            "locale": "en",
            "firstResult": "0",
            "numberOfResults": "250",
            "excerptLength": "150",
            "enableDidYouMean": True,
            "sortCriteria": "relevancy",
            "queryFunctions": [],
            "rankingFunctions": [],
            "facets": [],
            "facetOptions": {},
            "categoryFacets": [],
            "retrieveFirstSentences": True,
            "timezone": "America/New_York",
            "enableQuerySyntax": False,
            "enableDuplicateFiltering": False,
            "enableCollaborativeRating": False,
            "debug": False,
            "context": {
                        "productName": managed_product_name, "targetOids": target_oids
            },
            "allowQueriesWithoutKeywords": False
        }
        page = 1
        paginate = True
        try:
            while paginate:
                self.logger.info(f"{managed_product_name} - getting drivers page {page} - {json.dumps(payload)}")
                request = download_instance(link=api_url, method="POST", headers=headers, json=payload)
                if request.status_code != 200:
                    raise ConnectionError
                items = json.loads(request.text)
                results.extend(items["results"])
                first_results = int(payload["firstResult"])
                if int(payload["firstResult"]) < (items['totalCountFiltered'] - int(payload["numberOfResults"])):
                    page += 1
                    first_results += int(payload["numberOfResults"])
                    payload["firstResult"] = str(first_results)
                    continue
                paginate = False
        except (
                TimeoutError, ConnectionError, ConnectionRefusedError, ConnectionAbortedError, json.JSONDecodeError
        ) as e:
            (
                exception_type,
                _exception_object,
                exception_traceback,
            ) = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            error = {
                "url": api_url,
                "errorType": str(exception_type),
                "errorMsg": str(e),
                "source": "",
                "service": f"{str(filename)} - line {line_number}",
            }
            self.logger.error(f"API connection error - {json.dumps(error)}")
            raise ConnectionError("Vendor integration error - HPE data APIs are not available") from e

        # iterate items
        filtered_items = list()
        for document in results:
            if document['raw']['kmswitemid'] in self.bug_ids:
                self.dedup_count += 1
                continue
            self.bug_ids.add(document['raw']['kmswitemid'])

            sw_data = dict()
            sw_data["vendorLastUpdatedDate"] = datetime.datetime.strptime(
                document["raw"]['kmswitemupdatedate'][:10], "%m/%d/%Y"
            )
            # 1. filter bugs ( +2 days ) older than the lastExecution date
            if (sw_data["vendorLastUpdatedDate"] + datetime.timedelta(days=2)) <= earliest_bug_date:
                continue

            # 2. filter drivers based on severity levels
            priority = product_priorities.get(document["raw"]["kmswitemseverity"], None)
            if not priority:
                continue

            sw_data["bugId"] = document['raw']['kmswitemid']
            sw_data["bugUrl"] = f"https://support.hpe.com/hpesc/public/swd/detail?swItemId=" \
                                f"{document['raw']['kmswitemid']}"

            sw_data["description"] = f"Title: {document['raw']['kmswitemtitle_en']}\n" \
                                     f"Version: {document['raw']['kmswitemversion']}\n" \
                                     f"Operation Systems:  {', '.join(document['raw']['kmswtargetenvironment'])}\n" \
                                     f"Description: {document['raw']['description']}"

            sw_data["managedProductId"] = managed_product_id
            # convert sbPriority value to label
            sw_data["priority"] = priority
            sw_data["processed"] = 0
            sw_data["snCiTable"] = ""
            sw_data["snCiFilter"] = ""
            sw_data["summary"] = document['raw']['description']

            sw_data["vendorId"] = self.vendor_id
            sw_data["vendorData"] = {
                "bugProductNames":
                    document["raw"]["kmswtargetproductl1l5namelist"] if 'kmswtargetproductl1l5namelist' in
                                                                        document["raw"] else "",
                "bugProductIds": document["raw"]['kmswtargetproduct'],
                "bugConcepts": document["raw"]["sysconcepts"] if "sysconcepts" in document["raw"] else ""
            }

            filtered_items.append(sw_data)

        return filtered_items

    def get_document_details(self, doc_id):
        """
        download and parse doc details
        :param doc_id:
        :return:
        """
        xpaths = {
            "affected_hardware": '//*[@class="product_group_names"]//text()',
            "affected_software": '//*[@class="software_group_names"]//text()',
            "affected_operating_system": '//*[@class="operating_system_groups"]//text()',
            "description": '//*[@class="content.description"]//text()',
            "scope": '//*[@class="scope"]//text()',
            "resolution": '//*[@class="resolution"]//text()',
        }
        url = f"https://support.hpe.com/hpesc/public/api/document/{doc_id}?docLocale=en_US&ignorePayload=true"
        request_details = {"doc_id": doc_id, "url": url}
        self.logger.info(f"downloading document html - {json.dumps(request_details, default=str)}")
        response = download_instance(link=url, headers=[])
        data_fields = {k: "" for k in xpaths}
        if not response:
            self.logger.error("cant download/parse document html data")
            return data_fields
        root = lxml.html.fromstring(response.text)

        for section, xpath in xpaths.items():
            container = root.xpath(xpath)
            container = [x.strip() for x in container if x.strip()]
            if container:
                data_fields[section] = "\n".join(container[1:])
        return data_fields

    def get_products(self, product_type="", max_results=1000):
        """
        get all hpe products for a given filter query
        :return:
        """
        products = []
        headers = {
            "Authorization": f"{self.hpe_auth}",
            "Accept": "application/json",
        }

        api_url = f"https://platform.cloud.coveo.com/rest/search/v2?organizationId=" \
                  f"{self.resource_descriptions['organization_id']['resource_name']}"
        payload = {
            "isGuestUser": False,
            "cq": f'@source=="{self.resource_descriptions["product_search"]["resource_name"]}"',
            "searchHub": "HPE-Product-Page",
            "tab": "Products",
            "locale": "en",
            "firstResult": "0",
            "numberOfResults": f"{max_results}",
            "excerptLength": "150",
            "enableDidYouMean": True,
            "sortCriteria": "relevancy",
            "queryFunctions": [],
            "rankingFunctions": [],
            "facets": [
                {
                    "facetId": "@kmpmlevel1name",
                    "field": "kmpmlevel1name",
                    "type": "specific",
                    "injectionDepth": 1000,
                    "filterFacetCount": True,
                    "currentValues": [
                        {
                            "value": f"{product_type}",
                            "state": "selected"
                        },
                    ],
                    "numberOfValues": 8,
                    "freezeCurrentValues": False,
                    "preventAutoSelect": False,
                    "isFieldExpanded": False
                }
            ],
            "facetOptions": {},
            "categoryFacets": [],
            "retrieveFirstSentences": "true",
            "timezone": "America/New_York",
            "enableQuerySyntax": "false",
            "enableDuplicateFiltering": "false",
            "enableCollaborativeRating": "false",
            "debug": True,
            "context": {
                "tracking_id": "HPESCYIL2@SEr-yme9z9WYG-algAAAC0",
                "active_features":
                    "DCS,DHFWS,SA2,cep2_active,cep2_eligible,cep2_hpe_org,enablePatchStorage,"
                    "sa2_software_indexer_v2_toggle,sa2_ui_enable_token_client_caching,toggleCsr",
                "user_tracking_id": "YILa0UJGF1ucdm3VEEi2qQAAAIE"
            },
            "allowQueriesWithoutKeywords": "true"
        }
        page = 1
        paginate = True
        try:
            while paginate:
                self.logger.info(f"getting '{product_type}' products page {page} - {json.dumps(payload)}")
                request = requests.post(url=api_url, headers=headers, json=payload)
                if request.status_code != 200:
                    raise ConnectionError
                results = json.loads(request.text)

                # if the first page does not return any result - there is a problem with the coveo api
                # could be that the cq field in the post payload has to be updated the source is located here:
                # https://support.hpe.com/connect/resource/1627456369000/DCESearchProperties
                if page == 1 and not results["results"]:
                    self.logger.error("payload error - the api has returned 0 results")
                    raise ConnectionError

                products.extend(results["results"])
                first_results = int(payload["firstResult"])
                if int(payload["firstResult"]) < (results['totalCountFiltered'] - int(payload["numberOfResults"])):
                    page += 1
                    first_results += int(payload["numberOfResults"])
                    payload["firstResult"] = str(first_results)
                    continue
                paginate = False
        except (TimeoutError, ConnectionError, ConnectionRefusedError, ConnectionAbortedError) as e:
            (
                exception_type,
                _exception_object,
                exception_traceback,
            ) = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            error = {
                "url": api_url,
                "errorType": str(exception_type),
                "errorMsg": str(e),
                "source": "",
                "service": f"{str(filename)} - line {line_number}",
            }
            self.logger.error(json.dumps(error))
            raise ConnectionError("Vendor sync error - HPE data APIs are not available") from e

        return products

    def gen_auth_form(self, aura_config):
        """
        generate auth form used to gen auth token
        :param aura_config:
        :return:
        """
        form = dict()
        form["message"] = {
            "actions": [
                {
                    "id": "87;a",
                    "descriptor": "apex://DCEHPESearchController/ACTION$getToken",
                    "callingDescriptor": "markup://c:dceCoveoSearchCustomEndpointHandler",
                    "params": {}
                },
                {
                    "id": "89;a",
                    "descriptor": "apex://CoveoV2.ContentHandlerController/ACTION$getLoader",
                    "callingDescriptor": "markup://CoveoV2:ContentHandler",
                    "params": {
                        "loaderParams": {
                            "name": "dceHPESearch"
                        },
                        "componentType": "search"
                    }
                },
                {
                    "id": "99;a",
                    "descriptor": "apex://DCEHPESearchController/ACTION$supportedOidAssetCount",
                    "callingDescriptor": "markup://c:dceHPESearch",
                    "params": {}
                },
                {
                    "id": "100;a",
                    "descriptor": "apex://DCEHPESearchController/ACTION$getUserAuthentication",
                    "callingDescriptor": "markup://c:dceHPESearch",
                    "params": {}
                }
            ]
        }
        form["aura.context"] = {"mode": "PROD", "fwuid": aura_config['context']['fwuid'],
                                "app": "siteforce:communityApp",
                                "loaded":
                                    {
                                        "APPLICATION@markup://siteforce:communityApp":
                                            aura_config['context']['loaded']
                                            ['APPLICATION@markup://siteforce:communityApp']
                                    }, "dn": [], "globals": {}, "uad": False
                                }
        form_string = f"message={json.dumps(form['message'], separators=(',', ':'))}" \
                      f"&aura.context={json.dumps(form['aura.context'], separators=(',', ':'))}" \
                      f"&aura.pageURI=/connect/s/search?language=en_US#q=7271228&t=Products&sort=relevancy" \
                      f"&numberOfResults=25&aura.token=undefined"
        self.logger.info(f"'{self.vendor_id}' - auth form generated | {form_string}")
        return form_string

    def get_aura_config(self):
        """
        aura is managing the public authentication, the config is located in the html page
        :return:
        """
        url = "https://support.hpe.com/connect/s/search?language=en_US"
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,"
                      "*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Host": "support.hpe.com",
            "sec-ch-ua": '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/95.0.4638.54 Safari/537.36"
        }
        self.logger.info(f"'{self.vendor_id}' - getting aura config | {url}")
        response = download_instance(link=url, headers=headers)
        config_container = re.findall("(?<=var auraConfig = ).*?}(?=;)", response.text)
        if not config_container:
            raise ConnectionError("Vendor sync error - HPE data APIs are not available")
        config = json.loads(config_container[0])
        return config

    def get_auth_key(self, auth_form):
        """
        retrieve hpe's public auth cred from support.hpe.com
        :return:
        """
        url = "https://support.hpe.com/connect/s/sfsites/aura?r=3&CoveoV2.ContentHandler.getLoader=1" \
              "&other.DCEHPESearch.getToken=1&other.DCEHPESearch.getUserAuthentication=1" \
              "&other.DCEHPESearch.supportedOidAssetCount=1"
        try:
            response = download_instance(
                method="POST",
                post_form=auth_form,
                link=url
            )
            if not response:
                raise ConnectionError()
            data = json.loads(response.text)
            self.hpe_auth = f'Bearer {json.loads(data["actions"][0]["returnValue"])["token"]}'
            self.logger.info(f"'{self.vendor_id}' - auth token successfully generated")

            # includes simplejson.decoder.JSONDecodeError
        except (ConnectionError, ValueError, json.JSONDecodeError) as e:
            (
                exception_type,
                _exception_object,
                exception_traceback,
            ) = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            error = {
                "url": "https://support.hpe.com/hpesc/public/km/api/coveo/search/token",
                "errorType": str(exception_type),
                "errorMsg": str(e),
                "source": "",
                "service": f"{str(filename)} - line {line_number}",
            }
            self.logger.error(f"API connection error - {json.dumps(error)}")
            raise ConnectionError("Vendor sync error - HPE data APIs are not available") from e

    @staticmethod
    def timestamp_format(time_str):
        """
        convert datetime objects to unified datetime string
        :param time_str:
        :return:
        """
        # max 6 digit micro seconds
        time_str = time_str.strip("Z")[:25] + "Z"
        known_formats = ["%m/%d/%Y %H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"]
        for fmt in known_formats:
            try:
                fmt_time = datetime.datetime.strptime(time_str[:26], fmt)
                return fmt_time
            except ValueError:
                continue
        return False

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
