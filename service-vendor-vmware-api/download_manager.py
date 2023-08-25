"""
created 2021-08-02

"""
import logging
import time

import requests


def request_instance(url, session, post, ignore_404=False, form_data=False, json=False, headers="", retry=5,
                     logger=logging.getLogger(__name__)):
    """

    :param url:
    :param session:
    :param headers:
    :param form_data:
    :param post:
    :param retry:
    :param logger:
    :param ignore_404: ignore 404 response
    :param json:
    :return:
    """
    tries = 0
    while tries < retry:
        try:
            if json:
                request = requests.post(url=url, timeout=20, headers=headers, json=json)
            elif post:
                if session:
                    request = session.post(url=url, timeout=20, headers=headers, data=form_data)
                else:
                    request = requests.post(url=url, timeout=20, headers=headers, data=form_data)
            else:
                if session:
                    if headers:
                        request = session.get(url=url, timeout=20, headers=headers)
                    else:
                        request = session.get(url=url, timeout=20)
                else:
                    if headers:
                        request = requests.get(url=url, timeout=20, headers=headers)
                    else:
                        request = requests.get(url=url, timeout=20)

            if request.status_code in [404, 401, 403]:
                if ignore_404:
                    request.status_code = 200
                    return request
                logger.error(
                    "{}: Download failed with status code {} - {}".format(
                        request.url, request.status_code, request.text
                    )
                )
                return False

            if request.status_code != 200:
                logger.error(
                    "{}: Download failed with status code {} - {} tries left".format(
                        request.url, request.status_code, tries
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
            logger.error(f"{url}: connection error - trying again in 10 sec - {tries} tries left")
            time.sleep(10)
            tries += 1

            continue

    logger.error(f"{url}: Download failed with with max retires")
    return False
