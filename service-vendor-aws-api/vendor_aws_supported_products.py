"""
  config for vendor_aws_bug_service.py supported products
  Attributes:
        https://docs.aws.amazon.com/config/latest/developerguide/resource-config-reference.html
      - service_name: service reference for aws cost explorer api
      - service_id: service reference for aws health api
      - sysparm_query: query to get CIs if SN query is supported
      - sysparm_fields: fields to return for the SN query if supported
      - bypass_inventory: indicates if a managedProduct should be created if the service is not included in inventory
      - min_usage_threshold: minimal value to be considered an active service
  """

supported_services = [
    {
        "service_name": "AWS Step Functions",
        "service_id": "STEPFUNCTIONS",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "AWS Storage Gateway",
        "service_id": "STORAGEGATEWAY",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon Simple Email Service",
        "service_id": "SES",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon Route 53",
        "service_id": "ROUTE53",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": True,
        "min_usage_threshold": 0
    },
    {
        "service_name": "AWS RoboMaker",
        "service_id": "ROBOMAKER",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon Managed Streaming for Apache Kafka",
        "service_id": "KAFKA",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "AWS Greengrass",
        "service_id": "GREENGRASS",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0

    },
    {
        "service_name": "AWS Glue",
        "service_id": "GLUE",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon Glacier",
        "service_id": "GLACIER",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon Forecast",
        "service_id": "FORECAST",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon ElastiCache",
        "service_id": "ELASTICACHE",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon Elastic Container Service for Kubernetes",
        "service_id": "EKS",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "AWS Data Exchange",
        "service_id": "DATAEXCHANGE",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon Comprehend",
        "service_id": "COMPREHEND",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "CodeGuru",
        "service_id": "CODEGURUREVIEWER",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "AWS CodeArtifact",
        "service_id": "CODEARTIFACT",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon CloudFront",
        "service_id": "CLOUDFRONT",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": True,
        "min_usage_threshold": 0
    },
    {
        "service_name": "AWS Certificate Manager",
        "service_id": "CERTIFICATEMANAGER",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon AppStream",
        "service_id": "APPSTREAM",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon Braket",
        "service_id": "BRAKET",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon API Gateway",
        "service_id": "APIGATEWAY",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "AWS CloudFormation",
        "service_id": "CLOUDFORMATION",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": True,
        "min_usage_threshold": 0
    },
    {
        "service_name": "AWS CloudTrail",
        "service_id": "CLOUDTRAIL",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 1000
    },
    {
        "service_name": "AmazonCloudWatch",
        "service_id": "CLOUDWATCH",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": True,
        "min_usage_threshold": 0
    },
    {
        "service_name": "CodeBuild",
        "service_id": "CODEBUILD",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "AWS Config",
        "service_id": "CONFIG",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": 'Amazon Elastic Compute Cloud - Compute',
        "service_id": "EC2",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "AWS Key Management Service",
        "service_id": "KMS",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "AWS Lambda",
        "service_id": "LAMBDA",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon Relational Database Service",
        "service_id": "RDS",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon Simple Storage Service",
        "service_id": "S3",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon Simple Notification Service",
        "service_id": "SNS",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "AWS Secrets Manager",
        "service_id": "SECRETSMANAGER",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon DynamoDB",
        "service_id": "DYNAMODB",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0.000001
    },
    {
        "service_name": "Amazon Kinesis",
        "service_id": "KINESIS",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon Kinesis Analytics",
        "service_id": "KINESISANALYTICS",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon Redshift",
        "service_id": "REDSHIFT",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    },
    {
        "service_name": "Amazon Simple Queue Service",
        "service_id": "SQS",
        "sysparm_fields": "",
        "sysparm_query": "",
        "bypass_inventory": False,
        "min_usage_threshold": 0
    }
]
