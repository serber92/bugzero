#!/usr/bin/env python3
"""
created 2021/12/17
"""
import datetime
import logging

import boto3
import dns.resolver

logger = logging.getLogger()


class ActiveRegionHasChangedError(Exception):
    """
    raised when the active region has changed
    """


class RegionLookupError(Exception):
    """
    raised when there was a problem when looking up the active region
    """


class HealthClient:
    """
    client for AWS health API
    """
    __active_region = None
    __client = None

    def __init__(self, aws_access_key_id, aws_secret_access_key, aws_session_token):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_session_token = aws_session_token

    def client(self):
        """

        :return:
        """
        if not HealthClient.__active_region:
            HealthClient.__active_region = self.active_region()
        else:
            current_active_region = self.active_region()
            if current_active_region != HealthClient.__active_region:
                old_active_region = HealthClient.__active_region
                HealthClient.__active_region = current_active_region

                if HealthClient.__client:
                    HealthClient.__client = None

                raise ActiveRegionHasChangedError(
                    'Active region has changed from [' + old_active_region + '] to [' + current_active_region + ']'
                )

        if not HealthClient.__client:
            HealthClient.__client = boto3.client(
                'health', region_name=HealthClient.__active_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                aws_session_token=self.aws_session_token
            )

        return HealthClient.__client

    @staticmethod
    def active_region():
        """

        :return:
        """
        qname = 'global.health.amazonaws.com'
        try:
            answers = dns.resolver.resolve(qname, 'CNAME')
        except Exception as e:
            raise RegionLookupError('Failed to resolve {}'.format(qname), e) from e
        if len(answers) != 1:
            raise RegionLookupError('Failed to get a single answer when resolving {}'.format(qname))
        name = str(answers[0].target)  # e.g. health.us-east-1.amazonaws.com.
        # region name is the 1st in split('.') -> ['health', 'us-east-1', 'amazonaws', 'com', '']
        region_name = name.split('.')[1]
        return region_name

    def event_details(self, event):
        """

        :param event:
        :return:
        """
        # NOTE: It is more efficient to call describe_event_details with a batch
        # of eventArns, but for simplicity of this demo we call it with a
        # single eventArn
        event_details_response = self.client().describe_event_details(eventArns=[event['arn']])
        return event_details_response['successfulSet']

    def describe_events(self, service):
        """
        Describe events using the same default filters as the Personal Health
        Return all open or upcoming events which started in the last 90 days ordered by event lastUpdatedTime
        :param service:
        :return:
        """
        events_paginator = self.client().get_paginator('describe_events')
        events_pages = events_paginator.paginate(filter={
            'startTimes': [
                {
                    'from': datetime.datetime.now() - datetime.timedelta(days=90)
                }
            ],
            'eventStatusCodes': ['open', 'upcoming', "closed"],
            'services': [service],
        })

        number_of_matching_events = 0
        detailed_events = []
        for events_page in events_pages:
            for event in events_page['events']:
                number_of_matching_events += 1
                event_details = self.event_details(event)
                for ev in event_details:
                    detailed_events.append(ev)

        return detailed_events
