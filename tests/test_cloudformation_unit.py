"""Unit tests for CloudFormation template validation."""

from pathlib import Path

import pytest
import yaml


class CloudFormationLoader(yaml.SafeLoader):
    """Custom YAML loader that handles CloudFormation intrinsic functions."""

    pass


def construct_ref(loader, node):
    """Handle !Ref tags."""
    return {"Ref": loader.construct_scalar(node)}


def construct_getatt(loader, node):
    """Handle !GetAtt tags."""
    if isinstance(node, yaml.ScalarNode):
        return {"Fn::GetAtt": loader.construct_scalar(node).split(".")}
    elif isinstance(node, yaml.SequenceNode):
        return {"Fn::GetAtt": loader.construct_sequence(node)}


def construct_sub(loader, node):
    """Handle !Sub tags."""
    return {"Fn::Sub": loader.construct_scalar(node)}


def construct_join(loader, node):
    """Handle !Join tags."""
    return {"Fn::Join": loader.construct_sequence(node)}


def construct_if(loader, node):
    """Handle !If tags."""
    return {"Fn::If": loader.construct_sequence(node)}


def construct_equals(loader, node):
    """Handle !Equals tags."""
    return {"Fn::Equals": loader.construct_sequence(node)}


def construct_not(loader, node):
    """Handle !Not tags."""
    return {"Fn::Not": loader.construct_sequence(node)}


def construct_and(loader, node):
    """Handle !And tags."""
    return {"Fn::And": loader.construct_sequence(node)}


def construct_or(loader, node):
    """Handle !Or tags."""
    return {"Fn::Or": loader.construct_sequence(node)}


def construct_base64(loader, node):
    """Handle !Base64 tags."""
    return {"Fn::Base64": loader.construct_scalar(node)}


def construct_cidr(loader, node):
    """Handle !Cidr tags."""
    return {"Fn::Cidr": loader.construct_sequence(node)}


def construct_find_in_map(loader, node):
    """Handle !FindInMap tags."""
    return {"Fn::FindInMap": loader.construct_sequence(node)}


def construct_import_value(loader, node):
    """Handle !ImportValue tags."""
    return {"Fn::ImportValue": loader.construct_scalar(node)}


def construct_select(loader, node):
    """Handle !Select tags."""
    return {"Fn::Select": loader.construct_sequence(node)}


def construct_split(loader, node):
    """Handle !Split tags."""
    return {"Fn::Split": loader.construct_sequence(node)}


def construct_transform(loader, node):
    """Handle !Transform tags."""
    return {"Fn::Transform": loader.construct_mapping(node)}


# Add constructors for CloudFormation intrinsic functions
CloudFormationLoader.add_constructor("!Ref", construct_ref)
CloudFormationLoader.add_constructor("!GetAtt", construct_getatt)
CloudFormationLoader.add_constructor("!Sub", construct_sub)
CloudFormationLoader.add_constructor("!Join", construct_join)
CloudFormationLoader.add_constructor("!If", construct_if)
CloudFormationLoader.add_constructor("!Equals", construct_equals)
CloudFormationLoader.add_constructor("!Not", construct_not)
CloudFormationLoader.add_constructor("!And", construct_and)
CloudFormationLoader.add_constructor("!Or", construct_or)
CloudFormationLoader.add_constructor("!Base64", construct_base64)
CloudFormationLoader.add_constructor("!Cidr", construct_cidr)
CloudFormationLoader.add_constructor("!FindInMap", construct_find_in_map)
CloudFormationLoader.add_constructor("!ImportValue", construct_import_value)
CloudFormationLoader.add_constructor("!Select", construct_select)
CloudFormationLoader.add_constructor("!Split", construct_split)
CloudFormationLoader.add_constructor("!Transform", construct_transform)


class TestCloudFormationTemplate:
    """Test CloudFormation template syntax and required resources."""

    @pytest.fixture
    def template_path(self):
        """Get path to CloudFormation template."""
        return Path(__file__).parent.parent / "infrastructure" / "template.yaml"

    @pytest.fixture
    def template_content(self, template_path):
        """Load CloudFormation template content."""
        with open(template_path, encoding="utf-8") as f:
            return f.read()

    @pytest.fixture
    def template_data(self, template_content):
        """Parse CloudFormation template as YAML with CloudFormation functions support."""
        return yaml.load(template_content, Loader=CloudFormationLoader)

    def test_template_file_exists(self, template_path):
        """Test that CloudFormation template file exists."""
        assert template_path.exists(), "CloudFormation template file should exist"
        assert template_path.is_file(), "CloudFormation template should be a file"

    def test_template_yaml_syntax(self, template_data):
        """Test that CloudFormation template has valid YAML syntax."""
        assert template_data is not None, "Template should parse as valid YAML"
        assert isinstance(template_data, dict), "Template should be a YAML dictionary"

    def test_template_format_version(self, template_data):
        """Test that template has correct CloudFormation format version."""
        assert "AWSTemplateFormatVersion" in template_data
        assert template_data["AWSTemplateFormatVersion"] == "2010-09-09"

    def test_template_has_description(self, template_data):
        """Test that template has a description."""
        assert "Description" in template_data
        assert isinstance(template_data["Description"], str)
        assert len(template_data["Description"]) > 0

    def test_template_has_parameters(self, template_data):
        """Test that template has required parameters."""
        assert "Parameters" in template_data
        parameters = template_data["Parameters"]

        # Required parameters for generic configuration
        required_params = [
            "BotName",
            "RSSFeedUrls",
            "TelegramChatId",
            "TelegramBotToken",
            "ScheduleExpression",
            "ScheduleTimezone",
        ]

        for param in required_params:
            assert param in parameters, f"Parameter {param} should be defined"
            assert "Type" in parameters[param], f"Parameter {param} should have Type"
            assert (
                "Description" in parameters[param]
            ), f"Parameter {param} should have Description"

    def test_template_has_resources(self, template_data):
        """Test that template has required AWS resources."""
        assert "Resources" in template_data
        resources = template_data["Resources"]

        # Required resources based on requirements
        required_resources = [
            "DeduplicationTable",  # DynamoDB table (Req 3.2)
            "ProcessorFunction",  # Lambda function (Req 3.3)
            "ProcessorSchedule",  # EventBridge scheduler (Req 3.4, 8.1)
            "DeadLetterQueue",  # SQS DLQ (Req 3.5, 8.3, 10.1)
            "LambdaLogGroup",  # CloudWatch log group (Req 3.6, 10.5)
            "TelegramBotSecret",  # Secrets Manager (Req 9.1)
            "LambdaExecutionRole",  # IAM role (Req 9.3)
            "SchedulerRole",  # Scheduler IAM role
        ]

        for resource in required_resources:
            assert resource in resources, f"Resource {resource} should be defined"
            assert (
                "Type" in resources[resource]
            ), f"Resource {resource} should have Type"

    def test_dynamodb_table_configuration(self, template_data):
        """Test DynamoDB table configuration for deduplication."""
        resources = template_data["Resources"]
        table = resources["DeduplicationTable"]

        assert table["Type"] == "AWS::DynamoDB::Table"

        properties = table["Properties"]
        assert "BillingMode" in properties
        assert properties["BillingMode"] == "PAY_PER_REQUEST"

        # Check TTL configuration (Requirement 5.5)
        assert "TimeToLiveSpecification" in properties
        ttl_spec = properties["TimeToLiveSpecification"]
        assert ttl_spec["AttributeName"] == "ttl"
        assert ttl_spec["Enabled"] is True

        # Check key schema
        assert "KeySchema" in properties
        key_schema = properties["KeySchema"]
        assert len(key_schema) == 1
        assert key_schema[0]["AttributeName"] == "item_id"
        assert key_schema[0]["KeyType"] == "HASH"

    def test_lambda_function_configuration(self, template_data):
        """Test Lambda function configuration."""
        resources = template_data["Resources"]
        function = resources["ProcessorFunction"]

        assert function["Type"] == "AWS::Lambda::Function"

        properties = function["Properties"]
        assert properties["Runtime"] == "python3.12"
        assert properties["Handler"] == "src.lambda_handler.lambda_handler"

        # Check environment variables
        assert "Environment" in properties
        env_vars = properties["Environment"]["Variables"]
        required_env_vars = [
            "TELEGRAM_SECRET_NAME",
            "TELEGRAM_CHAT_ID",
            "DYNAMODB_TABLE",
            "RSS_FEED_URLS",
            "AWS_REGION",
        ]

        for env_var in required_env_vars:
            assert (
                env_var in env_vars
            ), f"Environment variable {env_var} should be defined"

        # Check dead letter queue configuration (Requirement 8.3, 10.1)
        assert "DeadLetterConfig" in properties
        assert "TargetArn" in properties["DeadLetterConfig"]

    def test_eventbridge_scheduler_configuration(self, template_data):
        """Test EventBridge scheduler configuration for Europe/Rome timezone."""
        resources = template_data["Resources"]
        schedule = resources["ProcessorSchedule"]

        assert schedule["Type"] == "AWS::Scheduler::Schedule"

        properties = schedule["Properties"]
        assert "ScheduleExpression" in properties
        assert "ScheduleExpressionTimezone" in properties
        assert "Target" in properties

        # Check target configuration
        target = properties["Target"]
        assert "Arn" in target
        assert "RoleArn" in target

    def test_sqs_dead_letter_queue_configuration(self, template_data):
        """Test SQS Dead Letter Queue configuration."""
        resources = template_data["Resources"]
        queue = resources["DeadLetterQueue"]

        assert queue["Type"] == "AWS::SQS::Queue"

        properties = queue["Properties"]
        assert "MessageRetentionPeriod" in properties
        assert "VisibilityTimeoutSeconds" in properties

        # Check retention period (14 days = 1209600 seconds)
        assert properties["MessageRetentionPeriod"] == 1209600

    def test_secrets_manager_configuration(self, template_data):
        """Test Secrets Manager configuration for Telegram token."""
        resources = template_data["Resources"]
        secret = resources["TelegramBotSecret"]

        assert secret["Type"] == "AWS::SecretsManager::Secret"

        properties = secret["Properties"]
        assert "Description" in properties
        assert "SecretString" in properties

    def test_cloudwatch_log_group_configuration(self, template_data):
        """Test CloudWatch Log Group configuration."""
        resources = template_data["Resources"]
        log_group = resources["LambdaLogGroup"]

        assert log_group["Type"] == "AWS::Logs::LogGroup"

        properties = log_group["Properties"]
        assert "RetentionInDays" in properties

    def test_iam_role_minimal_privileges(self, template_data):
        """Test IAM role has minimal required privileges."""
        resources = template_data["Resources"]
        role = resources["LambdaExecutionRole"]

        assert role["Type"] == "AWS::IAM::Role"

        properties = role["Properties"]
        assert "Policies" in properties

        policies = properties["Policies"]
        policy_names = [policy["PolicyName"] for policy in policies]

        # Check required policies for minimal privileges (Requirement 9.3, 9.4, 9.5, 9.6)
        required_policies = [
            "DynamoDBAccess",
            "SecretsManagerAccess",
            "BedrockAccess",
            "CloudWatchMetrics",
            "SQSDeadLetterQueue",
        ]

        for policy_name in required_policies:
            assert (
                policy_name in policy_names
            ), f"Policy {policy_name} should be defined"

    def test_template_has_outputs(self, template_data):
        """Test that template has required outputs for monitoring."""
        assert "Outputs" in template_data
        outputs = template_data["Outputs"]

        # Required outputs for monitoring and management
        required_outputs = [
            "LambdaFunctionName",
            "LambdaFunctionArn",
            "DynamoDBTableName",
            "DeadLetterQueueUrl",
            "SecretsManagerSecretName",
            "CloudWatchLogGroup",
            "MonitoringDashboardUrl",
        ]

        for output in required_outputs:
            assert output in outputs, f"Output {output} should be defined"
            assert (
                "Description" in outputs[output]
            ), f"Output {output} should have Description"
            assert "Value" in outputs[output], f"Output {output} should have Value"

    def test_parameter_constraints(self, template_data):
        """Test parameter constraints and validation."""
        parameters = template_data["Parameters"]

        # Test BotName constraints
        bot_name = parameters["BotName"]
        assert "AllowedPattern" in bot_name
        assert "ConstraintDescription" in bot_name

        # Test TelegramChatId constraints
        chat_id = parameters["TelegramChatId"]
        assert "AllowedPattern" in chat_id
        assert chat_id["AllowedPattern"] == "^-?[0-9]+$"

        # Test TelegramBotToken security
        bot_token = parameters["TelegramBotToken"]
        assert bot_token.get("NoEcho") is True
        assert "MinLength" in bot_token

        # Test LambdaMemorySize allowed values
        memory_size = parameters["LambdaMemorySize"]
        assert "AllowedValues" in memory_size
        allowed_values = memory_size["AllowedValues"]
        assert 512 in allowed_values  # Default value should be in allowed values

    def test_resource_tagging(self, template_data):
        """Test that resources have appropriate tags."""
        resources = template_data["Resources"]

        # Resources that should have tags
        tagged_resources = [
            "DeduplicationTable",
            "TelegramBotSecret",
            "DeadLetterQueue",
            "LambdaLogGroup",
            "LambdaExecutionRole",
            "ProcessorFunction",
        ]

        for resource_name in tagged_resources:
            resource = resources[resource_name]
            properties = resource["Properties"]

            assert "Tags" in properties, f"Resource {resource_name} should have tags"
            tags = properties["Tags"]

            # Check for Application tag
            app_tags = [tag for tag in tags if tag["Key"] == "Application"]
            assert (
                len(app_tags) > 0
            ), f"Resource {resource_name} should have Application tag"

    def test_monitoring_dashboard_configuration(self, template_data):
        """Test CloudWatch monitoring dashboard configuration."""
        resources = template_data["Resources"]

        # Check if monitoring dashboard exists
        assert "MonitoringDashboard" in resources
        dashboard = resources["MonitoringDashboard"]

        assert dashboard["Type"] == "AWS::CloudWatch::Dashboard"

        properties = dashboard["Properties"]
        assert "DashboardBody" in properties

        # The dashboard body uses CloudFormation !Sub function
        dashboard_body = properties["DashboardBody"]

        # Handle CloudFormation intrinsic function
        if isinstance(dashboard_body, dict) and "Fn::Sub" in dashboard_body:
            dashboard_content = dashboard_body["Fn::Sub"]
        else:
            dashboard_content = dashboard_body

        # Check it contains expected metric names
        assert "ExecutionSuccess" in dashboard_content
        assert "ExecutionFailure" in dashboard_content
        assert "FeedsProcessed" in dashboard_content
        assert "ItemsFound" in dashboard_content
        assert "MessagesSent" in dashboard_content
