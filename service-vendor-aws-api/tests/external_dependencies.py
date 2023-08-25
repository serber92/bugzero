"""
a collection of mock variables and methods
"""
import datetime
import logging
import os

import requests
from sqlalchemy.exc import OperationalError

root_folder = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger()

# -------------------------------------------------------------------------------------------------------------------- #
#                                                 MOCK VARIABLES                                                       #
# -------------------------------------------------------------------------------------------------------------------- #
mock_bug_table_class = type("bugs", (object, ), {
    **{x: type("mock", (object,),
               {"prop": type("mock", (object,),
                             {"columns": [
                                 type("managedProduct", (object,), {"type": 1}),
                                 type("bugs", (object,), {"type": 1}),
                             ]
                             },
                             ),
                }) for x in ["vendorData", "snCiFilter", "snCiTable", "bugId", "managedProductId",
                             "vendorLastUpdatedDate"]
       },
    **{
        "__init__": lambda *_args, **_kwargs: None,
    }
})
mock_managed_product = [
    type("managedProduct", (object,),
         {"lastExecution": datetime.datetime.utcnow() - datetime.timedelta(hours=10),
          "id": 1, "name": "AWS Lambda", "isDisabled": 0,
          "vendorData": {"vendorRegions": ["us-east-1"], "vendorEventScopes": ["Account Specific"]},
          "vendorPriorities": [{"snPriority": "1|1|1", "vendorPriority": "Issue"}],
          "vendorStatuses": ["Open"],

          }
         )
]
mock_disabled_managed_product = [
    type("managedProduct", (object,), {"lastExecution": 1, "name": 'AWS Lambda', "isDisabled": 1, "id": 1}),
]
mock_just_processed_managed_product = [
    type("managedProduct", (object,), {"lastExecution": datetime.datetime.utcnow() - datetime.timedelta(hours=3),
                                       "name": 'AWS Lambda', "isDisabled": 0,
                                       "vendorData": {"osMajorVersions": "1"},
                                       "id": 1
                                       }
         ),
]
mock_sn_ci_query_response_json_missing_description_field = [
    {"sn_query_url": "test", "sys_id": "test"}
]
mock_sn_ci_query_response_json = [
    {"sn_query_url": "test", "sys_id": "test", "version": "5.1.2"}
]
mock_sn_ci_query_response_no_version = [
    {"sn_query_url": "test", "sys_id": "test", "version": ""}
]
mock_sn_ci_query_response_json_empty = [
]
mock_varchar_table = type("test", (object, ), {
    **{x: type("mock", (object,),
               {"prop": type("mock", (object,),
                             {"columns": [
                                 type("bugs", (object,), {
                                     "type":  type("type", (object,), {
                                         "type": "test", "length": 8
                                     }),
                                 }),
                             ]
                             },
                             ),
                }) for x in ["vendorData", "snCiFilter", "snCiTable", "bugId", "managedProductId",
                             "vendorLastUpdatedDate"]
       },
    **{
        "__init__": lambda *_args, **_kwargs: None,
    }
})
mock_session = type("session", (object,), {
    "post": lambda **_kwargs: type("sessionPost", (object,), {"status_code": 200}),
    "get": lambda **_kwargs: type("sessionPost", (object,), {"status_code": 200}),
})
mock_session_w_post_404 = type("session", (object,), {
    "post": lambda **_kwargs:
    type("sessionPost", (object,), {"status_code": 404, "url": "http://failed-url.com", "text": ""})
})
mock_health_events = [
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_ISSUE",
            "eventTypeCategory": "issue",
            "region": "us-east-1",
            "startTime": "",
            "endTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": ""
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "us-east-1",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "us-east-1",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "us-east-1",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "us-east-1",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    }
]
mock_health_events_different_event_scope = [
    {
            "event": {
                "arn": "",
                "service": "LAMBDA",
                "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_ISSUE",
                "eventTypeCategory": "accountNotification",
                "region": "us-east-2",
                "startTime": "",
                "endTime": "",
                "lastUpdatedTime": "",
                "statusCode": "closed",
                "eventScopeCode": "PUBLIC"
            },
            "eventDescription": {
                "latestDescription": ""
            }
        },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "accountNotification",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": "",
            "statusCode": "open",
            "eventScopeCode": "PUBLIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "accountNotification",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": "",
            "statusCode": "open",
            "eventScopeCode": "PUBLIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "accountNotification",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": "",
            "statusCode": "open",
            "eventScopeCode": "PUBLIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "accountNotification",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": "",
            "statusCode": "open",
            "eventScopeCode": "PUBLIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    }
]
mock_health_events_different_priorities = [
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_ISSUE",
            "eventTypeCategory": "accountNotification",
            "region": "us-east-2",
            "startTime": "",
            "endTime": "",
            "lastUpdatedTime": "",
            "statusCode": "closed",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": ""
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "accountNotification",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": "",
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "accountNotification",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": "",
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "accountNotification",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": "",
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "accountNotification",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": "",
            "statusCode": "open",
            "eventScopeCode": "PUBLIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    }
]
mock_health_events_old_entries = [
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_ISSUE",
            "eventTypeCategory": "issue",
            "region": "us-east-2",
            "startTime": "",
            "endTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-11-24 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "closed",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": ""
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-11-24 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-11-24 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-11-24 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-11-24 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "open",
            "eventScopeCode": "PUBLIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    }
]
mock_health_events_different_status = [
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_ISSUE",
            "eventTypeCategory": "issue",
            "region": "us-east-2",
            "startTime": "",
            "endTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "closed",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": ""
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "closed",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "closed",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "closed",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "global",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "closed",
            "eventScopeCode": "PUBLIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    }
]
mock_health_events_different_region = [
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_ISSUE",
            "eventTypeCategory": "issue",
            "region": "us-east-2",
            "startTime": "",
            "endTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": ""
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "us-east-2",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "us-east-2",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "us-east-2",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "open",
            "eventScopeCode": "ACCOUNT_SPECIFIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    },
    {
        "event": {
            "arn": "",
            "service": "LAMBDA",
            "eventTypeCode": "AWS_LAMBDA_OPERATIONAL_NOTIFICATION",
            "eventTypeCategory": "issue",
            "region": "us-east-2",
            "startTime": "",
            "lastUpdatedTime": datetime.datetime.strptime("2021-12-31 15:15:36", "%Y-%m-%d %H:%M:%S"),
            "statusCode": "open",
            "eventScopeCode": "PUBLIC"
        },
        "eventDescription": {
            "latestDescription": "You are receiving this message because we identified that your account created or"
                                 "updated or invoked Lambda functions on or after July 1, 2021.\n\nAWS Lambda is "
                                 "extending the capability to track the current state of a function through its "
                                 "lifecycle to all functions [1]. With this change, you may need to update your "
        }
    }
]
mock_formatted_bugs = [
        {
            "id": 13753,
            "bugId": "1638919396",
            "bugUrl": "https://phd.aws.amazon.com/phd/home#/event-log?eventID=arn:aws:health:us-east-1::event/",
            "description": "[RESOLVED] Elevated Errors and Latencies\n\n[03:23 PM PST] We continue to see increased",
            "priority": "Issue",
            "snCiFilter": "install_status=1^operational_status=1",
            "snCiTable": "cmdb_model?sysparm_query=status=In%20Production^manufacturer.name=AWS",
            "summary": "Aws Apigateway Operational Issue - us-east-1 - Public Issue - AWS_APIGATEWAY_OPERATIO",
            "status": "Closed",
            "knownAffectedReleases": "AWS Gateway API",
            "knownFixedReleases": None,
            "knownAffectedHardware": None,
            "knownAffectedOs": None,
            "vendorData": "{}",
            "versions": None,
            "vendorCreatedDate": "2021-12-07 18:23:16",
            "vendorLastUpdatedDate": "2021-12-10 17:48:39",
            "processed": 0,
            "createdAt": "2021-12-21 18:56:59",
            "updatedAt": "2021-12-21 18:56:59",
            "managedProductId": None,
            "vendorId": "aws"
        },
        {
            "id": 13754,
            "bugId": "1637780385",
            "bugUrl": "https://phd.aws.amazon.com/phd/home#/event-log?eventID=arn:aws:h",
            "description": "[RESOLVED] Increased API Error Rates\n\n[10:59 AM PST] We are investigating increased ",
            "priority": "Issue",
            "snCiFilter": "install_status=1^operational_status=1",
            "snCiTable": "cmdb_model?sysparm_query=status=In%20Production^manufacturer.name=AWS",
            "summary": "Aws Apigateway Operational Issue - us-east-2 - Public Issue -",
            "status": "Closed",
            "knownAffectedReleases": "AWS Gateway API",
            "knownFixedReleases": None,
            "knownAffectedHardware": None,
            "knownAffectedOs": None,
            "vendorData": "{}",
            "versions": None,
            "vendorCreatedDate": "2021-11-24 13:59:46",
            "vendorLastUpdatedDate": "2021-11-24 15:20:30",
            "processed": 0,
            "createdAt": "2021-12-21 18:56:59",
            "updatedAt": "2021-12-21 18:56:59",
            "managedProductId": None,
            "vendorId": "aws"
        },
        {
            "id": 13755,
            "bugId": "1249eeb2ba41f6a667cbbecbfc02df5048a4800fc3abbf72e8c54f8066cad1a7",
            "bugUrl": "https://phd.aws.amazon.com/phd/home#/event-log?eventID=arn:aws:health:glad1a7",
            "description": "We previously sent a notification on October 22 regarding an issue with CodeBuild builds",
            "priority": "Account Notification",
            "snCiFilter": "install_status=1^operational_status=1",
            "snCiTable": "cmdb_model?sysparm_query=status=In%20Production^manufacturer.name=AWS",
            "summary": "Aws Codebuild Operational Notification - global - Accou",
            "status": "Open",
            "knownAffectedReleases": "AWS CodeBuild",
            "knownFixedReleases": None,
            "knownAffectedHardware": None,
            "knownAffectedOs": None,
            "vendorData": "{}",
            "versions": None,
            "vendorCreatedDate": "2021-10-23 01:35:00",
            "vendorLastUpdatedDate": "2021-10-23 02:29:16",
            "processed": 0,
            "createdAt": "2021-12-21 18:57:00",
            "updatedAt": "2021-12-21 21:00:15",
            "managedProductId": 870,
            "vendorId": "aws"
        },
        {
            "id": 13756,
            "bugId": "aa563b302e08957cca299440d6be4f9e7927bfdce223cfff44aa4fc22c69a784",
            "bugUrl": "https://phd.aws.amazon.com/phd/home#/event-log?eventID=arn:aws:health:global::",
            "description": "We are reaching out to you because you ran a CodeBuild build using an AWS managed dockere",
            "priority": "Account Notification",
            "snCiFilter": "install_status=1^operational_status=1",
            "snCiTable": "cmdb_model?sysparm_query=status=In%20Production^manufacturer.name=AWS",
            "summary": "Aws Codebuild Operational Notification - global - Account Specific Accountnotification",
            "status": "Open",
            "knownAffectedReleases": "AWS CodeBuild",
            "knownFixedReleases": None,
            "knownAffectedHardware": None,
            "knownAffectedOs": None,
            "vendorData": "{}",
            "versions": None,
            "vendorCreatedDate": "2021-10-22 04:20:00",
            "vendorLastUpdatedDate": "2021-10-22 05:13:37",
            "processed": 0,
            "createdAt": "2021-12-21 18:57:00",
            "updatedAt": "2021-12-21 21:00:15",
            "managedProductId": 870,
            "vendorId": "aws"
        },
        {
            "id": 13757,
            "bugId": "1637779569",
            "bugUrl": "https://phd.aws.amazon.com/phd/home#/event-log?eventID=arn:aws:health:us-east-2::",
            "description": "[RESOLVED] Increased Error Rates\n\n[10:46 AM PST] We are investigating i",
            "priority": "Issue",
            "snCiFilter": "install_status=1^operational_status=1",
            "snCiTable": "cmdb_model?sysparm_query=status=In%20Production^manufacturer.name=AWS",
            "summary": "Aws Lambda Operational Issue - us-east-2 - Public Issue - AWS_LAMBDA_OPERAT",
            "status": "Closed",
            "knownAffectedReleases": "AWS Lambda",
            "knownFixedReleases": None,
            "knownAffectedHardware": None,
            "knownAffectedOs": None,
            "vendorData": "{}",
            "versions": None,
            "vendorCreatedDate": "2021-11-24 13:46:10",
            "vendorLastUpdatedDate": "2021-11-24 15:15:36",
            "processed": 0,
            "createdAt": "2021-12-21 18:57:01",
            "updatedAt": "2021-12-21 21:00:16",
            "managedProductId": 872,
            "vendorId": "aws"
        },
        {
            "id": 13758,
            "bugId": "2dec471318f155b24bc18dc47fd8afacb089b5ba39d310945d75559b85011d06",
            "bugUrl": "https://phd.aws.amazon.com/phd/home#/event-log?eventID=arn:aws:health:gl",
            "description": "You are receiving this message because we identified that your account ",
            "priority": "Account Notification",
            "snCiFilter": "install_status=1^operational_status=1",
            "snCiTable": "cmdb_model?sysparm_query=status=In%20Production^manufacturer.name=AWS",
            "summary": "Aws Lambda Operational Notification - global - Account Specific Acco",
            "status": "Open",
            "knownAffectedReleases": "AWS Lambda",
            "knownFixedReleases": None,
            "knownAffectedHardware": None,
            "knownAffectedOs": None,
            "vendorData": "{}",
            "versions": None,
            "vendorCreatedDate": "2021-10-12 10:30:00",
            "vendorLastUpdatedDate": "2021-10-14 17:57:07",
            "processed": 0,
            "createdAt": "2021-12-21 18:57:01",
            "updatedAt": "2021-12-21 21:00:16",
            "managedProductId": 872,
            "vendorId": "aws"
        },
        {
            "id": 13759,
            "bugId": "1633447956",
            "bugUrl": "https://phd.aws.amazon.com/phd/home#/event-log?eventID=arn:aws:health:eu-west-1",
            "description": "[RESOLVED] Increased invoke timeouts\n\n[08:32 AM PDT] We are investigating increased ",
            "priority": "Issue",
            "snCiFilter": "install_status=1^operational_status=1",
            "snCiTable": "cmdb_model?sysparm_query=status=In%20Production^manufacturer.name=AWS",
            "summary": "Aws Lambda Operational Issue - eu-west-1 - Public Issue - AWS_LAMBDA_OPERATIO",
            "status": "Closed",
            "knownAffectedReleases": "AWS Lambda",
            "knownFixedReleases": None,
            "knownAffectedHardware": None,
            "knownAffectedOs": None,
            "vendorData": "{}",
            "versions": None,
            "vendorCreatedDate": "2021-10-05 11:32:36",
            "vendorLastUpdatedDate": "2021-10-05 18:17:42",
            "processed": 0,
            "createdAt": "2021-12-21 18:57:01",
            "updatedAt": "2021-12-21 21:00:16",
            "managedProductId": 872,
            "vendorId": "aws"
        },
        {
            "id": 13760,
            "bugId": "1636495106",
            "bugUrl": "https://phd.aws.amazon.com/phd/home#/event-log?eventID=arn:aws:he",
            "description": "[RESOLVED] Elevated API Error Rates\n\n[01:58 PM PST] We are investigating increased 5xx",
            "priority": "Issue",
            "snCiFilter": "install_status=1^operational_status=1",
            "snCiTable": "cmdb_model?sysparm_query=status=In%20Production^manufacturer.name=AWS",
            "summary": "Aws S3 Operational Issue - us-east-1 - Public Issue - AWS_S3_OPERATIONAL_ISSUE_KEGOD_16",
            "status": "Closed",
            "knownAffectedReleases": "AWS S3",
            "knownFixedReleases": None,
            "knownAffectedHardware": None,
            "knownAffectedOs": None,
            "vendorData": "{}",
            "versions": None,
            "vendorCreatedDate": "2021-11-09 16:58:27",
            "vendorLastUpdatedDate": "2021-11-09 22:51:25",
            "processed": 0,
            "createdAt": "2021-12-21 18:57:01",
            "updatedAt": "2021-12-21 21:00:17",
            "managedProductId": 874,
            "vendorId": "aws"
        },
        {
            "id": 13761,
            "bugId": "1638021361",
            "bugUrl": "https://phd.aws.amazon.com/phd/home#/event-log?eventID=arn:",
            "description": "[RESOLVED] Increased Latency and Error Rates\n\n[05:56 AM PST] We are investigating ",
            "priority": "Issue",
            "snCiFilter": "install_status=1^operational_status=1",
            "snCiTable": "cmdb_model?sysparm_query=status=In%20Production^manufacturer.name=AWS",
            "summary": "Aws Sns Operational Issue - us-west-2 - Public Issue - AWS_SNS_OPERATIONAL",
            "status": "Closed",
            "knownAffectedReleases": "AWS Simple Notification Service",
            "knownFixedReleases": None,
            "knownAffectedHardware": None,
            "knownAffectedOs": None,
            "vendorData": "{}",
            "versions": None,
            "vendorCreatedDate": "2021-11-27 08:56:01",
            "vendorLastUpdatedDate": "2021-11-27 09:42:19",
            "processed": 0,
            "createdAt": "2021-12-21 18:57:01",
            "updatedAt": "2021-12-21 21:00:17",
            "managedProductId": 875,
            "vendorId": "aws"
        }
    ]


# -------------------------------------------------------------------------------------------------------------------- #
#                                                 MOCK ClASSES                                                         #
# -------------------------------------------------------------------------------------------------------------------- #
class MockLastExecution(int):
    """
    last execution variable for DB class
    """
    def is_(self, *_args):
        """

        :param _args:
        :return:
        """
        if self:
            return None
        else:
            return None


class SessionMock:
    """
    requests session mock that raises a connection error on post
    """
    @staticmethod
    def post(url, timeout, headers, data):
        """

        :param url:
        :param timeout:
        :param headers:
        :param data:
        :return:
        """
        raise requests.exceptions.ConnectionError


class MockAwsApiClient:
    """
    :return:
    """
    def __init__(
            self,
            vendor_id="aws"
    ):
        """
        """
        self.bug_ids = set()
        self.dedup_count = 0
        self.bugs = dict()
        self.logger = logger
        self.service_now_ci_table = ""
        self.sn_query_cache = {}
        self.sn_versions = []
        self.vendor_id = vendor_id
        self.thread_error_tracker = 0
        self.kb_info_parse_errors = 0
        self.kb_failed_urls = []
        self.sn_table = ""

    @staticmethod
    def html_string_cleaner(text):
        return text

    @staticmethod
    def generate_sn_filter(*_args, **_kwargs):
        return "test"

    @staticmethod
    def timestamp_format(_time_str):
        return datetime.datetime.now()


class MockDbClient:
    """

    """
    def __init__(self, *_args, **_kwargs):
        """

        :param args:
        :param kwargs:
        """
        pass
    conn = type(
        "conn", (object,),
        {
            "commit": lambda **_kwargs: type("mockObject", (object,), {}),
            "refresh": lambda *_args, **_kwargs: mock_operational_error(),
            "add": lambda *_args: True,
            "query": lambda *_args, **_kwargs:
            type("query", (object,),
                 {"filter_by": lambda *_args, **_kwargs: type("mockObject", (object,), {
                     "first": lambda *_args: type("mockObject", (object,), {"active": True}),
                     "all": lambda *_args: [], },),
                  "get": lambda x: type("mockObject", (object,), {"value": True}),
                  "filter": lambda *_args, **_kwargs: type(
                      "mockObject", (object,), {
                          "or_": lambda *_args: type(
                              "mockObject", (object,), {"active": True}),
                          "all": lambda *_args: [],
                          "first": lambda *_args: False,
                      }
                  ),
                  },
                 )
        }
    )

    base = type(
        "base", (object,),
        {
            "classes": {
                "test": lambda **_kwargs: True,
                "testManagedProducts": type("mockClass", (object,),
                                            {"vendorId": True, "__init__": lambda *_args, **_kwargs: None}),
                "":  type("class", (object,), {"active": True}),

            }
        }
    )

    @staticmethod
    def create_session():
        """

        :return:
        """
        return True


class MockEmptyDbClient:
    """
    a db client instance that has zero bugs
    """
    def __init__(self, *_args, **_kwargs):
        """

        :param args:
        :param kwargs:
        """
        pass
    conn = type("conn", (object,), {
        "commit": lambda **_kwargs: type("query", (object,), {}),
        "add": lambda *_args: True,
        "query": lambda *_args, **_kwargs:
        type("query", (object,), {"filter_by": lambda *_args, **_kwargs: type("query", (object,), {
            "first": lambda *_args: type("query", (object,), {"active": True}),
            "all": lambda *_args: [], },),
                                  "get": lambda *_args, **_kwargs: False,
                                  }
             )
    })
    base = type("base", (object,), {
        "classes": {
            "test": lambda **_kwargs: True,
            "":  type("class", (object,), {"active": True}),

        }
    })

    @staticmethod
    def create_session():
        return True


class MockDbClientWithManagedProductsNoBugs:
    def __init__(self, *_args, **_kwargs):
        """
        db instance with managedProducts and 0 bugs
        :param args:
        :param kwargs:
        """
        pass
    conn = type(
        "conn", (object,),
        {
            "commit": lambda **_kwargs: type("query", (object,), {}),
            "add": lambda *_args: True,
            "query": lambda *_args, **_kwargs:
            type("query", (object,),
                 {
                     "filter": lambda *_args, **_kwargs: type(
                         "filter", (object,), {
                             "or_": lambda *_args: type(
                                 "or", (object,), {"active": True}),
                             "all": lambda *_args: mock_managed_product,
                             "first": lambda *_args: False,
                         }
                     ),
                     "filter_by":
                         lambda *_args, **_kwargs:
                         type("filter_by", (object,), {
                             "first": lambda *_args: type(
                                 "first", (object,), {"active": True}),
                             "all": lambda *_args: [], },
                              ),
                     "get": lambda x: type("query", (object,), {"value": {"snAuthToken": "", "snApiUrl": ""}}),
                 }
                 )
        }
    )

    base = type(
        "base", (object,),
        {
            "classes": {
                "bugs_table": mock_bug_table_class,
                "test": lambda **_kwargs: True,
                "managedProducts":  type(
                    "mockClass", (object,),
                    # managed products
                    {
                        "name": "test",
                        "lastExecution": MockLastExecution(),
                        "isDisabled": 1,
                        "vendorId": "aws"
                    }
                ),
                "": type(
                    "mockClass", (object,),
                    {
                        "name": "test",
                        "lastExecution": MockLastExecution(),
                        "isDisabled": 1,
                        "vendorId": "aws",
                        "id": "1",
                        "active": True,
                    }
                )


            }
        }
    )

    @staticmethod
    def create_session():
        return True


# -------------------------------------------------------------------------------------------------------------------- #
#                                                 MOCK METHODS                                                         #
# -------------------------------------------------------------------------------------------------------------------- #
def mock_database_init(self, db_host, db_user, db_password, db_port, db_name, base=None, conn=None):
    """
    set database connection variables in class instance
    """
    self.host = db_host
    self.username = db_user
    self.password = db_password
    self.port = int(db_port)
    self.dbname = db_name
    self.base = type("MockDBBase", (object,), {"classes": {
            "bugs": type("mockClass", (object,), {"bugId": ""}),
            "services": type("mockClass", (object,), {"id": ""}),
            "serviceExecution": lambda *_args, **_kwargs: ("mockClass", (object,), {"id": ""}),
        }
    }
                     )
    self.conn = type(
        "MockDBBase", (object,),
        {
            "add": lambda *_args, **_kwargs: True,
            "commit": lambda *_args, **_kwargs: True,
            "close": lambda *_args, **_kwargs: True,
            "query": lambda *_args, **_kwargs:
            type("mockObject", (object,),
                 {
                     "filter": lambda *_args, **_kwargs:
                     type("mockObject", (object,),
                          {
                              "first": lambda *_args, **_kwargs: type(
                                  "mockEntry", (object,), {
                                      "status": "", "lastExecution": "", "message": "", "lastSuccess": ""
                                  }
                              )
                          })
                 }
                 )
        },
    )


def mock_env():
    """
    mock environment variables
    :return:
    """
    return {
        "SETTINGS_TABLE": "", "MANAGED_PRODUCTS_TABLE": "managedProducts", "SERVICES_TABLE": "", "VENDORS_TABLE": "",
        "SERVICE_EXECUTION_TABLE": "", "DB_HOST": "", "DB_PORT": "3660", "DB_NAME": "", "DB_USER": "", "DB_PASS": "",
        "BUGS_TABLE": "", "AWS_DEFAULT_REGION": "us-east-1", "EVENT_CLASS": "", "NODE": "", "SNS_TOPIC": "",
        'CLIENT_ACCESS_ROLE': ''
    }


def mock_operational_error(*_args, **_kwargs):
    """
    force an sqlalchemy OperationalError
    :param _args:
    :param _kwargs:
    :return:
    """
    raise OperationalError("test", "test", "test")


def mock_requests_read_timeout(*_args, **_kwargs):
    """
    force a requests.exceptions.ReadTimeout
    :param _args:
    :param _kwargs:
    :return:
    """
    raise requests.exceptions.ReadTimeout("ReadTimeout")


def mock_requests_connection_timeout(*_args, **_kwargs):
    """
    force a requests.exceptions.ConnectTimeout
    :param _args:
    :param _kwargs:
    :return:
    """
    raise requests.exceptions.ConnectTimeout("ConnectTimeout")


def mock_requests_connection_error(*_args, **_kwargs):
    """
    force a requests.exceptions.ConnectionError
    :param _args:
    :param _kwargs:
    :return:
    """
    raise requests.exceptions.ConnectionError("ConnectionError")


def mock_connection_error(*_args, **_kwargs):
    """
    simulate a connectionError exception
    :param _args:
    :param _kwargs:
    :return:
    """
    raise ConnectionError("Vendor integration error - aws data APIs are not working properly")


def mock_managed_products_query_result_no_version(*_args, **_kwargs):
    """
    mocked list of 1 managedProduct with an empty productSoftwareVersions field
    :param _args:
    :param _kwargs:
    :return:
    """
    return [
        type("mockManagedProduct", (object,), {
            "vendorData": {"productSoftwareVersions": []},
            "add": lambda *_args: True,
            "name": "Test",
            "id": "test"
        })

    ]


def mock_managed_products_query_result(*_args, **_kwargs):
    """
    mocked list of 1 managedProduct with an empty productSoftwareVersions field
    :param _args:
    :param _kwargs:
    :return:
    """
    return [
        type("mockManagedProduct", (object,), {
            "vendorData": {"productSoftwareVersions": ["5.5.5"]},
            "add": lambda *_args: True,
            "name": "Test",
            "lastExecution": None,
            "id": "test"
        })

    ]
