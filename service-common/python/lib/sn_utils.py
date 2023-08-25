"""
created 2021-09-30
"""
import json


def sn_event_formatter(
  logger, event_class, resource, node, metric_name, error_type, severity, description, additional_info="",
  source="bugzero"):
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
    :param logger
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
    logger.info(f"generated SN event record - {json.dumps(event_record, default=str)}")
    return event_record


def sn_priority_2_label(value, logger):
    """
    convert sn priory values to labels
    " 1|1|1" ==> "1 - High / 1 - High / 1 - Critical"
    :param value:
    :param logger:
    :return:
    """
    try:
        priorities = {
          "1|1|1": "1 - High / 1 - High / 1 - Critical",
          "1|2|2": "1 - High / 2 - Medium / 2 - High",
          "2|1|2": "2 - Medium / 1 - High / 2 - High",
          "1|3|3": "1 - High / 3 - Low / 3 - Moderate",
          "2|2|3": "2 - Medium / 2 - Medium / 3 - Moderate",
          "2|3|4": "2 - Medium / 3 - Low / 4 - Low",
          "3|1|3": "3 - Low / 1 - High / 3 - Moderate",
          "3|2|4": "3 - Low / 2 - Medium / 4 - Low",
          "3|3|5": "3 - Low / 3 - Low / 5 - Planning"
        }
        return priorities[value]
    except KeyError:
        logger.error("{} is not a valid SN priority".format(value))
        return value
