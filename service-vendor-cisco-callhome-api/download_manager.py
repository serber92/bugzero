"""
created 2021-04-23
"""
import logging

import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def download_instance(link, headers, method='GET', retry=10, timeout=20):
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
    while tries < retry:
        try:
            request = requests.request(method=method, url=link, timeout=timeout, headers=headers)
            if request.status_code in [404, 401, 403]:
                logger.error(
                    "{}: Download failed with status code {} - {}".format(
                        request.url, request.status_code, request.text
                    )
                )
                tries += 1
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

    logger.error(f"{link}: Download failed with with max retires")
    return False
