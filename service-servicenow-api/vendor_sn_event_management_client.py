#!/usr/bin/env python3
"""
created 2021-09-30
"""
import json
import logging.config
import os

import requests
from requests.packages import urllib3

urllib3.disable_warnings()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, *_context):
    """
    format serviceNow event management records and post to the eventManagement endpoint, max 10 records per request
    :return:
    """
    sn_event_management_endpoint = f"{os.environ['BZ_SN_PORTAL_URL']}/api/global/em/jsonv2"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {os.environ['BZ_SN_PORTAL_BASIC_AUTH_KEY']}",
    }
    log_payload = {"success": True, "events": []}

    sns_source_verified = True
    error_message = ""
    if not event.get("Records", ""):
        error_message = f"missing 'Records' field in event object - {json.dumps(event, default=str)}"
        sns_source_verified = False

    elif not isinstance(event.get("Records", ""), list):
        error_message = f"Records object type must be one of [dict(array), list] not {str(type(event.get('Records')))}"
        sns_source_verified = False

    elif event["Records"][0].get("EventSource", "") != "aws:sns":
        error_message = f"not supported or missing EventSource - {event['Records'][0].get('EventSource', '')}"
        sns_source_verified = False

    if not sns_source_verified:
        log_payload["success"] = False
        log_payload["error_message"] = error_message
        logger.error(error_message)
        return {"message": json.dumps(log_payload, default=str)}

    events = [json.loads(r["Sns"]["Message"]) for r in event["Records"]]
    logger.info(f"new event - {json.dumps(event, default=str)}")

    # create groups of max 10 events
    record_groups = [
        events[i: i + 10] for i in range(0, len(events), 10)
    ]

    for i, g in enumerate(record_groups, start=1):
        payload = json.dumps({"records": list(g)}, default=str)
        logger.info(f"sn - posting events group {i}/{len(record_groups)} - {payload}")

        completed = False
        retry = 5
        while retry:
            try:
                response = requests.post(url=sn_event_management_endpoint, data=payload, headers=headers)
                if response.status_code != 200:
                    error_message = "{}: Download failed with status code {} - {} tries left".format(
                        response.url, response.status_code, retry
                    )
                    logger.error(error_message)
                    retry -= 1
                    continue
                completed = True
                break

            except requests.exceptions.RequestException as e:
                retry -= 1
                error_message = "{}: {} - {} tries left".format(sn_event_management_endpoint, str(e), retry)
                logger.error(error_message)

        event_status = "ok"
        failure_error = ""
        if not completed:
            failure_error = "{}: Download failed with with max retires".format(sn_event_management_endpoint)
            event_status = "error"
            log_payload["success"] = False
            log_payload["error_message"] = "one or more events failed to be published through the endpoint"

        log_payload["events"].append(
            {"records": list(g), "status": event_status, "error_message": failure_error}
        )
    logger.info(json.dumps(log_payload, default=str))
    return {"message": json.dumps(log_payload, default=str)}
