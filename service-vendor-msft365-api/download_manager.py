"""
created 2021-06-29

updated 2021-08-31
- added support for passed headers
"""
import logging

import requests


def download_instance(
        link, session, retry=3, logger=logging.getLogger(__name__), headers=None, method='GET', payload=None, json=None
):
    """
    simple http downloader
    :param link:
    :param retry:
    :param headers:
    :param payload:
    :param json:
    :param logger:
    :param session:
    :param method:
    :return:
    """
    tries = 0
    if not session and not headers:
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,he;q=0.8",
            "cache-control": "max-age=0",
            "cookie": "HttpOnly",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "cross-site",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/84.0.4147.89 Safari/537.36"
        }
    while tries < retry:
        try:
            if method == "POST":
                if session:
                    if headers:
                        request = session.post(url=link, data=payload, json=json, headers=headers, timeout=3)
                    else:
                        request = session.post(url=link, data=payload, json=json)
                else:
                    request = requests.post(headers=headers, url=link, data=payload)
            else:
                if session:
                    request = session.get(url=link, timeout=3, headers=headers, verify=False)
                else:
                    request = requests.get(url=link, timeout=3, headers=headers, verify=False)

            if request.status_code in [404, 401, 410, 411, 500]:
                if logger:
                    logger.error("{}: Download failed with status code {}".format(request.url, request.status_code))
                    return False

            if request.status_code != 200:
                if logger:
                    logger.warning("{}: Download failed with status code {}".format(request.url, request.status_code))
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
    if logger:
        logger.error("{}: Download failed with with max retires".format(link))
    return False
