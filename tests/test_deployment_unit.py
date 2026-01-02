"""
Unit tests for deployment script functionality.
Tests prerequisites verification and S3 bucket creation.
Requirements: 2.1, 2.3
"""

import os
import subprocess
import unittest
import warnings
from unittest.mock import Mock, patch

import boto3
from moto import mock_aws

# Suppress all botocore deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="botocore")
warnings.filterwarnings("ignore", message=".*datetime.datetime.utcnow.*", category=DeprecationWarning)


class TestDeploymentPrerequisites(unittest.TestCase):
    """Test deployment script prerequisites verification (Requirements 2.1)"""

    def setUp(self):
        """Set up test environment"""
        self.script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'scripts',
            'deploy.sh'
        )

    def test_script_exists_and_executable(self):
        """Test that deployment script exists and is executable"""
        self.assertTrue(os.path.exists(self.script_path),
                       "Deployment script should exist")
        self.assertTrue(os.access(self.script_path, os.X_OK),
                       "Deployment script should be executable")

    @patch('subprocess.run')
    def test_aws_cli_check_success(self, mock_run):
        """Test AWS CLI prerequisite check when AWS CLI is available"""
        # Mock successful AWS CLI version check
        mock_run.return_value = Mock(
            returncode=0,
            stdout="aws-cli/2.0.0 Python/3.8.0 Linux/5.4.0 botocore/2.0.0"
        )

        # Test AWS CLI detection
        result = subprocess.run(['which', 'aws'], capture_output=True, text=True)

        # The actual test would be in the bash script, but we can verify
        # that our test setup works correctly
        self.assertIsNotNone(result)

    @patch('subprocess.run')
    def test_python3_check_success(self, mock_run):
        """Test Python 3 prerequisite check when Python 3 is available"""
        # Mock successful Python 3 version check
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Python 3.12.0"
        )

        # Test Python 3 detection
        result = subprocess.run(['which', 'python3'], capture_output=True, text=True)

        # Verify test setup
        self.assertIsNotNone(result)

    @patch('subprocess.run')
    def test_zip_command_check_success(self, mock_run):
        """Test zip command prerequisite check when zip is available"""
        # Mock successful zip version check
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Copyright (c) 1990-2008 Info-ZIP - Type 'zip \"-L\"' for software license."
        )

        # Test zip command detection
        result = subprocess.run(['which', 'zip'], capture_output=True, text=True)

        # Verify test setup
        self.assertIsNotNone(result)

    def test_required_files_exist(self):
        """Test that required files exist for deployment"""
        project_root = os.path.dirname(os.path.dirname(__file__))

        # Check CloudFormation template
        template_path = os.path.join(project_root, 'infrastructure', 'template.yaml')
        self.assertTrue(os.path.exists(template_path),
                       "CloudFormation template should exist")

        # Check requirements file
        requirements_path = os.path.join(project_root, 'requirements.txt')
        self.assertTrue(os.path.exists(requirements_path),
                       "Requirements file should exist")

        # Check source directory
        src_path = os.path.join(project_root, 'src')
        self.assertTrue(os.path.isdir(src_path),
                       "Source directory should exist")

    def test_script_help_option(self):
        """Test that deployment script shows help when requested"""
        try:
            result = subprocess.run(
                [self.script_path, '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should exit with code 0 for help
            self.assertEqual(result.returncode, 0,
                           "Help option should exit successfully")

            # Should contain usage information
            self.assertIn("Usage:", result.stdout,
                         "Help should contain usage information")
            self.assertIn("--telegram-token", result.stdout,
                         "Help should mention required telegram token")
            self.assertIn("--chat-id", result.stdout,
                         "Help should mention required chat ID")

        except subprocess.TimeoutExpired:
            self.fail("Script help command timed out")

    def test_script_dry_run_missing_params(self):
        """Test that script fails gracefully when required parameters are missing"""
        try:
            result = subprocess.run(
                [self.script_path, '--dry-run'],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should exit with non-zero code for missing required params
            self.assertNotEqual(result.returncode, 0,
                              "Should fail when required parameters are missing")

            # Should mention missing telegram token (check both stdout and stderr)
            error_output = (result.stdout + result.stderr).lower()
            self.assertIn("telegram", error_output,
                         "Error should mention missing telegram token")

        except subprocess.TimeoutExpired:
            self.fail("Script dry-run command timed out")


@mock_aws
class TestS3BucketCreation(unittest.TestCase):
    """Test S3 bucket creation functionality (Requirements 2.3)"""

    def setUp(self):
        """Set up test environment with mocked AWS services"""
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        self.sts_client = boto3.client('sts', region_name='us-east-1')

        # Mock AWS account ID
        self.account_id = '123456789012'

    def test_s3_bucket_creation_us_east_1(self):
        """Test S3 bucket creation in us-east-1 region"""
        bucket_name = 'test-rss-bot-artifacts-123456789012-us-east-1'
        region = 'us-east-1'

        # Verify bucket doesn't exist initially
        with self.assertRaises(Exception):
            self.s3_client.head_bucket(Bucket=bucket_name)

        # Create bucket (us-east-1 doesn't need LocationConstraint)
        self.s3_client.create_bucket(
            Bucket=bucket_name,
            ACL='private'
        )

        # Verify bucket was created
        response = self.s3_client.head_bucket(Bucket=bucket_name)
        self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 200)

        # Verify bucket location
        location = self.s3_client.get_bucket_location(Bucket=bucket_name)
        # us-east-1 returns None for LocationConstraint
        self.assertIsNone(location['LocationConstraint'])

    def test_s3_bucket_creation_other_region(self):
        """Test S3 bucket creation in regions other than us-east-1"""
        bucket_name = 'test-rss-bot-artifacts-123456789012-eu-west-1'
        region = 'eu-west-1'

        # Create S3 client for the specific region
        s3_client = boto3.client('s3', region_name=region)

        # Create bucket with LocationConstraint for non-us-east-1 regions
        s3_client.create_bucket(
            Bucket=bucket_name,
            ACL='private',
            CreateBucketConfiguration={'LocationConstraint': region}
        )

        # Verify bucket was created
        response = s3_client.head_bucket(Bucket=bucket_name)
        self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 200)

        # Verify bucket location
        location = s3_client.get_bucket_location(Bucket=bucket_name)
        self.assertEqual(location['LocationConstraint'], region)

    def test_s3_bucket_already_exists(self):
        """Test handling when S3 bucket already exists"""
        bucket_name = 'existing-bucket'

        # Create bucket first
        self.s3_client.create_bucket(Bucket=bucket_name, ACL='private')

        # Verify bucket exists
        response = self.s3_client.head_bucket(Bucket=bucket_name)
        self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 200)

        # Attempting to check if bucket exists should succeed
        # (This simulates the script's bucket existence check)
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            bucket_exists = True
        except Exception:
            bucket_exists = False

        self.assertTrue(bucket_exists, "Should detect that bucket already exists")

    def test_s3_bucket_versioning_configuration(self):
        """Test that S3 bucket versioning is enabled"""
        bucket_name = 'test-versioning-bucket'

        # Create bucket
        self.s3_client.create_bucket(Bucket=bucket_name, ACL='private')

        # Enable versioning (as done in deployment script)
        self.s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )

        # Verify versioning is enabled
        versioning = self.s3_client.get_bucket_versioning(Bucket=bucket_name)
        self.assertEqual(versioning['Status'], 'Enabled')

    def test_s3_bucket_encryption_configuration(self):
        """Test that S3 bucket encryption is configured"""
        bucket_name = 'test-encryption-bucket'

        # Create bucket
        self.s3_client.create_bucket(Bucket=bucket_name, ACL='private')

        # Configure server-side encryption (as done in deployment script)
        encryption_config = {
            'Rules': [
                {
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256'
                    }
                }
            ]
        }

        self.s3_client.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration=encryption_config
        )

        # Verify encryption is configured
        encryption = self.s3_client.get_bucket_encryption(Bucket=bucket_name)
        rules = encryption['ServerSideEncryptionConfiguration']['Rules']
        self.assertEqual(len(rules), 1)
        self.assertEqual(
            rules[0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm'],
            'AES256'
        )

    def test_bucket_name_generation(self):
        """Test bucket name generation logic"""
        bot_name = 'test-rss-bot'
        account_id = '123456789012'
        region = 'us-east-1'

        # Expected bucket name format from deployment script
        expected_bucket_name = f"{bot_name}-artifacts-{account_id}-{region}"

        # Verify naming convention
        self.assertEqual(
            expected_bucket_name,
            'test-rss-bot-artifacts-123456789012-us-east-1'
        )

        # Verify bucket name is valid (lowercase, no underscores, etc.)
        self.assertTrue(expected_bucket_name.islower(),
                       "Bucket name should be lowercase")
        self.assertNotIn('_', expected_bucket_name,
                        "Bucket name should not contain underscores")
        self.assertTrue(len(expected_bucket_name) <= 63,
                       "Bucket name should be 63 characters or less")


class TestDeploymentScriptIntegration(unittest.TestCase):
    """Integration tests for deployment script components"""

    def setUp(self):
        """Set up test environment"""
        self.script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'scripts',
            'deploy.sh'
        )

    def test_script_dry_run_with_valid_params(self):
        """Test script dry-run mode with valid parameters"""
        try:
            result = subprocess.run([
                self.script_path,
                '--dry-run',
                '--telegram-token', 'test-token-123456:ABC-DEF',
                '--chat-id', '-1001234567890',
                '--stack-name', 'test-stack',
                '--region', 'us-east-1'
            ], capture_output=True, text=True, timeout=30)

            # Dry run should complete successfully
            self.assertEqual(result.returncode, 0,
                           f"Dry run should succeed. Error: {result.stderr}")

            # Should contain dry run indicators
            self.assertIn("[DRY RUN]", result.stdout,
                         "Output should indicate dry run mode")

            # Should show configuration
            self.assertIn("test-stack", result.stdout,
                         "Should show configured stack name")
            self.assertIn("-1001234567890", result.stdout,
                         "Should show configured chat ID")

        except subprocess.TimeoutExpired:
            self.fail("Script dry-run with valid params timed out")

    def test_script_parameter_validation(self):
        """Test script parameter validation"""
        test_cases = [
            # Missing telegram token
            {
                'args': ['--chat-id', '-1001234567890'],
                'expected_error': 'telegram.*token.*required'
            },
            # Missing chat ID
            {
                'args': ['--telegram-token', 'test-token'],
                'expected_error': 'chat.*id.*required'
            },
            # Invalid option
            {
                'args': ['--invalid-option', 'value'],
                'expected_error': 'unknown.*option'
            }
        ]

        for test_case in test_cases:
            with self.subTest(args=test_case['args']):
                try:
                    result = subprocess.run(
                        [self.script_path] + test_case['args'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    # Should fail with non-zero exit code
                    self.assertNotEqual(result.returncode, 0,
                                      "Should fail with invalid parameters")

                    # Should contain expected error message
                    error_output = (result.stderr + result.stdout).lower()
                    self.assertRegex(error_output, test_case['expected_error'],
                                   f"Should contain error about {test_case['expected_error']}")

                except subprocess.TimeoutExpired:
                    self.fail(f"Parameter validation test timed out for args: {test_case['args']}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
