"""
updated 2021-08-23
 improved download variables and methods
"""
import logging.config

import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def download_instance(link, headers=None, method='GET', post_form="", json="", retry=10, timeout=20):
    """
    simple http downloader
    :param link:
    :param retry:
    :param post_form:
    :param timeout:
    :param json:
    :param headers
    :param method
    :return:
    """
    tries = 0
    while tries < retry:
        try:
            if headers:
                if json:
                    request = requests.request(method=method, url=link, timeout=timeout, headers=headers, json=json)
                else:
                    request = requests.request(
                        method=method, url=link, timeout=timeout, headers=headers, data=post_form
                    )
            else:
                if json:
                    request = requests.request(method=method, timeout=timeout, url=link, json=json)
                else:
                    request = requests.request(method=method, timeout=timeout, url=link, data=post_form)

            if request.status_code in [404, 401, 403]:
                logger.error(
                    "{}: Download failed with status code {} - {}".format(
                        request.url, request.status_code, request.text
                    )
                )
                return False

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
    raise ConnectionError(f"{link}: Download failed with with max retires")
