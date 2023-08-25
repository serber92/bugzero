"""
created 2021-10-08
custom exception for vendor integration
"""


class VendorExceptions(Exception):
    """Base class for other exceptions"""
    def __init__(self, internal_message, event_message):
        self.internal_message = internal_message
        self.event_message = event_message
        super().__init__()


class LambdaTimeOutException(VendorExceptions):
    """
       raised when a lambda instance has reach the max time configured

       Attributes:
           url -- endpoint url
           event_message -- explanation of the error for the user
           message -- explanation of the error for dev team
   """

    def __init__(self):
        self.internal_message = "lambda instance has reached execution timeout"
        self.event_message = self.internal_message
        super().__init__(self.internal_message, self.event_message)

    def __str__(self):  # pragma: no cover
        return f'{self.internal_message}'


class ApiResponseError(VendorExceptions):
    """
        raised when parsing an API endpoint response fails

        Attributes:
            url -- endpoint url
            event_message -- explanation of the error for the user
            message -- explanation of the error for dev team
    """
    def __init__(self, url, internal_message, event_message):
        self.url = url
        self.internal_message = internal_message
        self.event_message = event_message
        super().__init__(self.internal_message, self.event_message)

    def __str__(self):  # pragma: no cover
        return f'{self.internal_message}'


class ApiRegexParseError(VendorExceptions):
    """
        raised when trying to find values from a API response using regex
        Attributes:
            url -- endpoint url
            event_message -- explanation of the error for the user
            message -- explanation of the error for dev team
            search_string -- original string searched with regex
            regex -- regex used for searching
    """
    def __init__(self, url, internal_message, event_message, search_string, regex):
        self.url = url
        self.search_string = search_string
        self.regex = regex
        self.internal_message = internal_message
        self.event_message = event_message
        super().__init__(self.internal_message, self.event_message)

    def __str__(self):  # pragma: no cover
        return f'{self.internal_message}'


class SnCiFieldMissing(VendorExceptions):
    """
        raised from IndexError when a Ci json does does not have a required field
        Attributes:
            url -- endpoint url
            event_message -- explanation of the error for the user
            message -- explanation of the error for dev team
            field_name -- required field
            ci_id -- unique ci sys_id
    """
    def __init__(self, url, internal_message, event_message, ci_sys_id, field_name):
        self.url = url
        self.field_name = field_name
        self.ci_id = ci_sys_id
        self.internal_message = internal_message
        self.event_message = event_message
        super().__init__(self.internal_message, self.event_message)

    def __str__(self):  # pragma: no cover
        return f'{self.internal_message}'


class ApiConnectionError(VendorExceptions):
    """
        raised when a connection attempt to the vendor API failed

        Attributes:
            url -- endpoint url
            event_message -- explanation of the error for the user
            message -- explanation of the error for dev team
    """
    def __init__(self, url, internal_message, event_message):
        self.url = url
        self.internal_message = internal_message
        self.event_message = event_message
        super().__init__(self.internal_message, self.event_message)

    def __str__(self):  # pragma: no cover
        return f'{self.internal_message}'


class VendorConnectionError(VendorExceptions):
    """
        raised when a connection attempt to an html page failed

        Attributes:
            url -- page url
            event_message -- explanation of the error for the user
            message -- explanation of the error for dev team
    """
    def __init__(self, url, internal_message, event_message):
        self.url = url
        self.internal_message = internal_message
        self.event_message = event_message
        super().__init__(self.internal_message, self.event_message)

    def __str__(self):  # pragma: no cover
        return f'{self.internal_message}'


class VendorResponseError(VendorExceptions):
    """
        raised when parsing an HTML page response fails

        Attributes:
            url -- endpoint url
            event_message -- explanation of the error for the user
            message -- explanation of the error for dev team
    """
    def __init__(self, url, internal_message, event_message):
        self.url = url
        self.internal_message = internal_message
        self.event_message = event_message
        super().__init__(self.internal_message, self.event_message)

    def __str__(self):  # pragma: no cover
        return f'{self.internal_message}'


class ServiceNotConfigured(VendorExceptions):
    """
        raised when a service configuration could not be retrieved from the env-db

        Attributes:
            service_id -- id of the service
            event_message -- explanation of the error for the user
            message -- explanation of the error for dev team
    """
    def __init__(self, service_id, internal_message, event_message):
        self.service_id = service_id
        self.internal_message = internal_message
        self.event_message = event_message
        super().__init__(self.internal_message, self.event_message)

    def __str__(self):  # pragma: no cover
        return f'{self.internal_message}'


class VendorDisabled(VendorExceptions):
    """
        raised when a vendor entry in the db is set isDisabled = 1
        generally this exception is logged internally and not handler
        Attributes:
            vendor_id -- id of vendor
            event_message -- explanation of the error for the user
            message -- explanation of the error for dev team
    """
    def __init__(self, vendor_id, internal_message, event_message):
        self.vendor_id = vendor_id
        self.internal_message = internal_message
        self.event_message = event_message
        super().__init__(self.internal_message, self.event_message)

    def __str__(self):  # pragma: no cover
        return f'{self.internal_message}'
