"""
updated 2021-08-23
 add 'method' option to requests
"""
import logging
from math import ceil
from time import sleep

import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def download_instance(link, headers, json=False, method='GET', retry=10, timeout=10, rate_limit_sleep=30):
    """
    simple http downloader
    :param link:
    :param retry:
    :param method:
    :param json:
    :param timeout:
    :param rate_limit_sleep:
    :param headers
    :return:
    """
    tries = 0
    while tries < retry:
        try:
            if json:
                request = requests.request(method=method, url=link, timeout=timeout, headers=headers, json=json)
            else:
                request = requests.request(method=method, url=link, timeout=timeout, headers=headers)

            if request.status_code in [404, 401, 403]:
                logger.error(
                    "{}: Download failed with status code {} - {}".format(
                        request.url, request.status_code, request.text
                    )
                )
                tries += 1
                continue

            if request.status_code == 429:
                try:
                    retry_after = ceil(float(request.headers.get('Retry-After')))
                except (KeyError, ValueError):
                    retry_after = rate_limit_sleep

                logger.error(
                    "{}: Download failed with status code {} - sleeping for {} seconds".format(
                        request.url, request.status_code, retry_after
                    )
                )
                sleep(retry_after)
                continue

            if request.status_code != 200:
                logger.error(
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
        except requests.exceptions.TooManyRedirects:
            break

    logger.error(f"{link}: Download failed with with max retires")
    return False
