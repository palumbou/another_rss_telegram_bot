#!/bin/bash

# Another RSS Telegram Bot - Deployment Script
# Generic serverless RSS-to-Telegram system deployment automation
# Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6

set -e  # Exit on any error

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_STACK_NAME="another-rss-telegram-bot"
DEFAULT_REGION="us-east-1"
DEFAULT_BOT_NAME="another-rss-telegram-bot"

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INFRASTRUCTURE_DIR="$PROJECT_ROOT/infrastructure"
SRC_DIR="$PROJECT_ROOT/src"
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
TEMPLATE_FILE="$INFRASTRUCTURE_DIR/template.yaml"

# Deployment artifacts
BUILD_DIR="$PROJECT_ROOT/build"
LAMBDA_ZIP="$BUILD_DIR/lambda-deployment-package.zip"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy Another RSS Telegram Bot to AWS

OPTIONS:
    -s, --stack-name STACK_NAME     CloudFormation stack name (default: $DEFAULT_STACK_NAME)
    -r, --region REGION             AWS region (default: $DEFAULT_REGION)
    -b, --bot-name BOT_NAME         Bot name for resource naming (default: $DEFAULT_BOT_NAME)
    -t, --telegram-token TOKEN      Telegram bot token (required for deploy)
    -c, --chat-id CHAT_ID           Telegram chat ID (required for deploy)
    -f, --feeds FEED_URLS           Comma-separated RSS feed URLs (optional, uses AWS defaults)
    --schedule EXPRESSION           EventBridge schedule expression (optional, default: daily 9 AM)
    --timezone TIMEZONE             Schedule timezone (optional, default: Europe/Rome)
    --bucket BUCKET_NAME            S3 bucket for artifacts (optional, auto-generated if not provided)
    --no-create-bucket              Don't create S3 bucket (assume it exists)
    --cleanup                       Delete all AWS resources created by this bot
    --dry-run                       Show what would be deployed without executing
    -h, --help                      Show this help message

EXAMPLES:
    # Basic deployment with required parameters
    $0 --telegram-token "123456:ABC-DEF..." --chat-id "-1001234567890"
    
    # Custom configuration
    $0 --stack-name "my-rss-bot" --region "eu-west-1" \\
       --telegram-token "123456:ABC-DEF..." --chat-id "-1001234567890" \\
       --feeds "https://example.com/feed1.xml,https://example.com/feed2.xml"
    
    # Cleanup all resources
    $0 --cleanup --region "eu-west-1"
    
    # Dry run to see what would be deployed
    $0 --telegram-token "123456:ABC-DEF..." --chat-id "-1001234567890" --dry-run

REQUIREMENTS:
    - AWS CLI configured with appropriate permissions
    - Python 3.12 or compatible version
    - zip command available
    - Internet connection for downloading dependencies

EOF
}

# Function to cleanup all AWS resources
cleanup_aws_resources() {
    local stack_name="$1"
    local region="$2"
    local bot_name="$3"
    local bucket_name="$4"
    
    print_header "Cleaning Up AWS Resources"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "[DRY RUN] Would cleanup the following resources:"
        print_status "- CloudFormation Stack: $stack_name"
        print_status "- S3 Bucket: $bucket_name"
        print_status "- Secrets Manager Secret: $bot_name-telegram-token"
        return 0
    fi
    
    # Delete CloudFormation stack
    print_status "Checking CloudFormation stack: $stack_name"
    if aws cloudformation describe-stacks --stack-name "$stack_name" --region "$region" &>/dev/null; then
        print_status "Deleting CloudFormation stack: $stack_name"
        aws cloudformation delete-stack --stack-name "$stack_name" --region "$region"
        
        print_status "Waiting for stack deletion to complete..."
        aws cloudformation wait stack-delete-complete --stack-name "$stack_name" --region "$region"
        print_success "CloudFormation stack deleted successfully"
    else
        print_warning "CloudFormation stack '$stack_name' not found"
    fi
    
    # Delete S3 bucket
    print_status "Checking S3 bucket: $bucket_name"
    if aws s3api head-bucket --bucket "$bucket_name" --region "$region" 2>/dev/null; then
        print_status "Emptying S3 bucket: $bucket_name"
        
        # Remove all current objects
        aws s3 rm "s3://$bucket_name" --recursive --region "$region" || true
        
        # Try to remove versioned objects (if versioning is enabled)
        print_status "Removing versioned objects (if any)..."
        aws s3api list-object-versions --bucket "$bucket_name" --region "$region" --query 'Versions[].{Key:Key,VersionId:VersionId}' --output text 2>/dev/null | \
        while read -r key version_id; do
            if [[ -n "$key" && -n "$version_id" ]]; then
                aws s3api delete-object --bucket "$bucket_name" --key "$key" --version-id "$version_id" --region "$region" || true
            fi
        done || true
        
        # Try to remove delete markers (if versioning is enabled)
        print_status "Removing delete markers (if any)..."
        aws s3api list-object-versions --bucket "$bucket_name" --region "$region" --query 'DeleteMarkers[].{Key:Key,VersionId:VersionId}' --output text 2>/dev/null | \
        while read -r key version_id; do
            if [[ -n "$key" && -n "$version_id" ]]; then
                aws s3api delete-object --bucket "$bucket_name" --key "$key" --version-id "$version_id" --region "$region" || true
            fi
        done || true
        
        print_status "Deleting S3 bucket: $bucket_name"
        aws s3api delete-bucket --bucket "$bucket_name" --region "$region"
        print_success "S3 bucket deleted successfully"
    else
        print_warning "S3 bucket '$bucket_name' not found"
    fi
    
    # Delete Secrets Manager secrets (find all secrets with bot name prefix)
    local secret_prefix="$bot_name-telegram-token"
    print_status "Checking Secrets Manager secrets with prefix: $secret_prefix"
    
    # List all secrets that start with the bot name prefix
    local secrets=$(aws secretsmanager list-secrets \
        --region "$region" \
        --query "SecretList[?starts_with(Name, '$secret_prefix')].Name" \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$secrets" ]]; then
        for secret_name in $secrets; do
            print_status "Deleting Secrets Manager secret: $secret_name"
            aws secretsmanager delete-secret \
                --secret-id "$secret_name" \
                --force-delete-without-recovery \
                --region "$region" || true
            print_success "Secret '$secret_name' deleted successfully"
        done
    else
        print_warning "No Secrets Manager secrets found with prefix '$secret_prefix'"
    fi
    
    # Clean up local build artifacts
    if [[ -d "$BUILD_DIR" ]]; then
        print_status "Cleaning up local build artifacts"
        rm -rf "$BUILD_DIR"
        print_success "Local build artifacts cleaned up"
    fi
    
    print_success "Cleanup completed successfully!"
}

# Function to check prerequisites (Requirements 2.1)
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing_deps=()
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        missing_deps+=("aws-cli")
        print_error "AWS CLI not found. Please install AWS CLI."
    else
        print_success "AWS CLI found: $(aws --version)"
        
        # Check AWS credentials
        if ! aws sts get-caller-identity &> /dev/null; then
            print_error "AWS credentials not configured or invalid. Please run 'aws configure'."
            exit 1
        else
            local aws_identity=$(aws sts get-caller-identity --output text --query 'Account')
            print_success "AWS credentials configured (Account: $aws_identity)"
        fi
    fi
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
        print_error "Python 3 not found. Please install Python 3.8 or later."
    else
        local python_version=$(python3 --version)
        print_success "Python found: $python_version"
        
        # Check if pip is available
        if ! python3 -m pip --version &> /dev/null; then
            print_warning "pip not found. Will attempt to install dependencies without pip."
        else
            print_success "pip found: $(python3 -m pip --version)"
        fi
    fi
    
    # Check zip command
    if ! command -v zip &> /dev/null; then
        missing_deps+=("zip")
        print_error "zip command not found. Please install zip utility."
    else
        print_success "zip command found: $(zip --version | head -n1)"
    fi
    
    # Check if required files exist
    if [[ ! -f "$TEMPLATE_FILE" ]]; then
        print_error "CloudFormation template not found at: $TEMPLATE_FILE"
        exit 1
    else
        print_success "CloudFormation template found"
    fi
    
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        print_error "Requirements file not found at: $REQUIREMENTS_FILE"
        exit 1
    else
        print_success "Requirements file found"
    fi
    
    if [[ ! -d "$SRC_DIR" ]]; then
        print_error "Source directory not found at: $SRC_DIR"
        exit 1
    else
        print_success "Source directory found"
    fi
    
    # Exit if any dependencies are missing
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        print_error "Please install the missing dependencies and try again."
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
}
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing_deps=()
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        missing_deps+=("aws-cli")
        print_error "AWS CLI not found. Please install AWS CLI."
    else
        print_success "AWS CLI found: $(aws --version)"
        
        # Check AWS credentials
        if ! aws sts get-caller-identity &> /dev/null; then
            print_error "AWS credentials not configured or invalid. Please run 'aws configure'."
            exit 1
        else
            local aws_identity=$(aws sts get-caller-identity --output text --query 'Account')
            print_success "AWS credentials configured (Account: $aws_identity)"
        fi
    fi
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
        print_error "Python 3 not found. Please install Python 3.8 or later."
    else
        local python_version=$(python3 --version)
        print_success "Python found: $python_version"
        
        # Check if pip is available
        if ! python3 -m pip --version &> /dev/null; then
            print_warning "pip not found. Will attempt to install dependencies without pip."
        else
            print_success "pip found: $(python3 -m pip --version)"
        fi
    fi
    
    # Check zip command
    if ! command -v zip &> /dev/null; then
        missing_deps+=("zip")
        print_error "zip command not found. Please install zip utility."
    else
        print_success "zip command found: $(zip --version | head -n1)"
    fi
    
    # Check if required files exist
    if [[ ! -f "$TEMPLATE_FILE" ]]; then
        print_error "CloudFormation template not found at: $TEMPLATE_FILE"
        exit 1
    else
        print_success "CloudFormation template found"
    fi
    
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        print_error "Requirements file not found at: $REQUIREMENTS_FILE"
        exit 1
    else
        print_success "Requirements file found"
    fi
    
    if [[ ! -d "$SRC_DIR" ]]; then
        print_error "Source directory not found at: $SRC_DIR"
        exit 1
    else
        print_success "Source directory found"
    fi
    
    # Exit if any dependencies are missing
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        print_error "Please install the missing dependencies and try again."
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
}

# Function to create S3 bucket for artifacts (Requirements 2.3)
create_s3_bucket() {
    local bucket_name="$1"
    local region="$2"
    
    print_header "Creating S3 Bucket for Artifacts"
    
    # Check if bucket already exists
    if aws s3api head-bucket --bucket "$bucket_name" --region "$region" 2>/dev/null; then
        print_success "S3 bucket '$bucket_name' already exists"
        return 0
    fi
    
    print_status "Creating S3 bucket: $bucket_name in region: $region"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "[DRY RUN] Would create S3 bucket: $bucket_name"
        return 0
    fi
    
    # Create bucket with appropriate configuration for region
    if [[ "$region" == "us-east-1" ]]; then
        # us-east-1 doesn't need LocationConstraint
        aws s3api create-bucket \
            --bucket "$bucket_name" \
            --region "$region" \
            --acl private
    else
        # Other regions need LocationConstraint
        aws s3api create-bucket \
            --bucket "$bucket_name" \
            --region "$region" \
            --acl private \
            --create-bucket-configuration LocationConstraint="$region"
    fi
    
    # Enable versioning for better artifact management
    aws s3api put-bucket-versioning \
        --bucket "$bucket_name" \
        --versioning-configuration Status=Enabled
    
    # Enable server-side encryption
    aws s3api put-bucket-encryption \
        --bucket "$bucket_name" \
        --server-side-encryption-configuration '{
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }'
    
    print_success "S3 bucket '$bucket_name' created successfully"
}

# Function to build and package Lambda function (Requirements 2.2)
build_lambda_package() {
    print_header "Building Lambda Deployment Package"
    
    # Clean and create build directory
    print_status "Preparing build directory"
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"
    
    # Create temporary directory for dependencies
    local temp_dir="$BUILD_DIR/temp"
    mkdir -p "$temp_dir"
    
    # Install Python dependencies
    print_status "Installing Python dependencies"
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "[DRY RUN] Would install dependencies from: $REQUIREMENTS_FILE"
    else
        # Install only production dependencies (exclude dev dependencies)
        python3 -m pip install \
            --target "$temp_dir" \
            --requirement "$REQUIREMENTS_FILE" \
            --no-deps \
            --quiet \
            feedparser boto3 requests beautifulsoup4 python-dateutil
        
        print_success "Dependencies installed successfully"
    fi
    
    # Copy source code
    print_status "Copying source code"
    cp -r "$SRC_DIR" "$temp_dir/"
    
    # Create deployment package
    print_status "Creating deployment package"
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "[DRY RUN] Would create Lambda zip package: $LAMBDA_ZIP"
    else
        cd "$temp_dir"
        zip -r "$LAMBDA_ZIP" . -q
        cd "$PROJECT_ROOT"
        
        local zip_size=$(du -h "$LAMBDA_ZIP" | cut -f1)
        print_success "Lambda package created: $LAMBDA_ZIP ($zip_size)"
    fi
}

# Function to upload Lambda package to S3
upload_lambda_package() {
    local bucket_name="$1"
    local region="$2"
    
    local s3_key="lambda-packages/$(basename "$LAMBDA_ZIP")"
    LAMBDA_S3_URI="s3://$bucket_name/$s3_key"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_header "Uploading Lambda Package to S3"
        print_status "[DRY RUN] Would upload Lambda package to: $LAMBDA_S3_URI"
        return 0
    fi
    
    print_header "Uploading Lambda Package to S3"
    print_status "Uploading to: $LAMBDA_S3_URI"
    aws s3 cp "$LAMBDA_ZIP" "$LAMBDA_S3_URI" --region "$region"
    
    # Wait for the file to be fully uploaded and available
    print_status "Verifying upload completion..."
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if aws s3api head-object --bucket "$bucket_name" --key "$s3_key" --region "$region" &>/dev/null; then
            print_success "Lambda package verified on S3"
            break
        else
            print_status "Waiting for upload to complete... (attempt $attempt/$max_attempts)"
            sleep 2
            ((attempt++))
        fi
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        print_error "Failed to verify Lambda package upload after $max_attempts attempts"
        exit 1
    fi
    
    print_success "Lambda package uploaded successfully"
}

# Function to create or update Secrets Manager secret (Requirements 2.4, 2.5)
manage_telegram_secret() {
    local secret_name="$1"
    local telegram_token="$2"
    local region="$3"
    
    print_header "Managing Telegram Bot Token in Secrets Manager"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "[DRY RUN] Would create/update secret: $secret_name"
        return 0
    fi
    
    # Check if secret already exists
    if aws secretsmanager describe-secret --secret-id "$secret_name" --region "$region" &>/dev/null; then
        print_status "Updating existing secret: $secret_name"
        aws secretsmanager update-secret \
            --secret-id "$secret_name" \
            --secret-string "$telegram_token" \
            --region "$region" \
            --output table
    else
        print_status "Creating new secret: $secret_name"
        # Try to create the secret
        if ! aws secretsmanager create-secret \
            --name "$secret_name" \
            --secret-string "$telegram_token" \
            --description "Telegram bot token for RSS Telegram Bot" \
            --region "$region" \
            --output table 2>/dev/null; then
            
            print_error "Failed to create secret. This might be due to a recently deleted secret with the same name."
            print_error "AWS Secrets Manager requires 7 days before reusing a secret name."
            print_error "Please try again with a different bot name or wait for the recovery period."
            exit 1
        fi
    fi
    
    print_success "Telegram bot token stored securely in Secrets Manager"
}

# Function to deploy CloudFormation stack (Requirements 2.6)
deploy_cloudformation() {
    local stack_name="$1"
    local region="$2"
    local bot_name="$3"
    local telegram_token="$4"
    local chat_id="$5"
    local feed_urls="$6"
    local schedule_expression="$7"
    local timezone="$8"
    local lambda_s3_uri="$9"
    local secret_name="${10}"
    
    print_header "Deploying CloudFormation Stack"
    
    # Extract bucket and key from S3 URI
    local s3_bucket=$(echo "$lambda_s3_uri" | sed 's|s3://||' | cut -d'/' -f1 | tr -d '[:space:]' | tr -d '[:cntrl:]')
    local s3_key=$(echo "$lambda_s3_uri" | sed 's|s3://[^/]*/||' | tr -d '[:space:]' | tr -d '[:cntrl:]')
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "[DRY RUN] Would deploy CloudFormation stack with parameters:"
        print_status "BotName=$bot_name"
        print_status "TelegramChatId=$chat_id"
        print_status "TelegramSecretName=$secret_name"
        print_status "LambdaS3Bucket=$s3_bucket"
        print_status "LambdaS3Key=$s3_key"
        print_status "RSSFeedUrls=$feed_urls"
        print_status "ScheduleExpression=$schedule_expression"
        print_status "ScheduleTimezone=$timezone"
        return 0
    fi
    
    print_status "Deploying stack: $stack_name"
    print_status "Template: $TEMPLATE_FILE"
    print_status "Region: $region"
    
    # Debug: Print parameter values
    print_status "Parameters:"
    print_status "  BotName: $bot_name"
    print_status "  TelegramChatId: $chat_id"
    print_status "  TelegramBotToken: [HIDDEN]"
    print_status "  TelegramSecretName: $secret_name"
    print_status "  LambdaS3Bucket: $s3_bucket"
    print_status "  LambdaS3Key: $s3_key"
    print_status "  RSSFeedUrls: $feed_urls"
    print_status "  ScheduleExpression: $schedule_expression"
    print_status "  ScheduleTimezone: $timezone"
    
    # Deploy the stack using individual parameter overrides
    aws cloudformation deploy \
        --template-file "$TEMPLATE_FILE" \
        --stack-name "$stack_name" \
        --parameter-overrides \
            "BotName=$bot_name" \
            "TelegramBotToken=$telegram_token" \
            "TelegramChatId=$chat_id" \
            "TelegramSecretName=$secret_name" \
            "LambdaS3Bucket=$s3_bucket" \
            "LambdaS3Key=$s3_key" \
            "RSSFeedUrls=$feed_urls" \
            "ScheduleExpression=$schedule_expression" \
            "ScheduleTimezone=$timezone" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$region" \
        --no-fail-on-empty-changeset
    
    print_success "CloudFormation stack deployed successfully"
}

# Function to display deployment results
show_deployment_results() {
    local stack_name="$1"
    local region="$2"
    
    print_header "Deployment Results"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "[DRY RUN] Deployment simulation completed"
        return 0
    fi
    
    print_status "Retrieving stack outputs..."
    
    # Get stack outputs
    local outputs=$(aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$region" \
        --query 'Stacks[0].Outputs' \
        --output table 2>/dev/null || echo "[]")
    
    if [[ "$outputs" != "[]" ]]; then
        echo -e "\n${GREEN}Stack Outputs:${NC}"
        echo "$outputs"
    fi
    
    # Show useful information
    echo -e "\n${GREEN}Deployment Summary:${NC}"
    echo "✅ Stack Name: $stack_name"
    echo "✅ Region: $region"
    echo "✅ Lambda Function: $bot_name-processor"
    echo "✅ DynamoDB Table: $bot_name-dedup"
    echo "✅ Secrets Manager: $bot_name-telegram-token"
    echo "✅ Dead Letter Queue: $bot_name-dlq"
    
    echo -e "\n${BLUE}Monitoring:${NC}"
    echo "📊 CloudWatch Logs: /aws/lambda/$bot_name-processor"
    echo "📈 CloudWatch Dashboard: $bot_name-monitoring"
    echo "🔍 AWS Console: https://$region.console.aws.amazon.com/lambda/home?region=$region#/functions/$bot_name-processor"
    
    echo -e "\n${YELLOW}Next Steps:${NC}"
    echo "1. Monitor the Lambda function logs for any issues"
    echo "2. Test the bot by triggering the Lambda function manually"
    echo "3. Check the CloudWatch dashboard for metrics"
    echo "4. Verify messages are being sent to your Telegram chat"
    
    print_success "Deployment completed successfully!"
}

# Main deployment function
main() {
    # Default values
    local stack_name="$DEFAULT_STACK_NAME"
    local region="$DEFAULT_REGION"
    local bot_name="$DEFAULT_BOT_NAME"
    local telegram_token=""
    local chat_id=""
    local feed_urls="https://aws.amazon.com/blogs/aws/feed/,https://aws.amazon.com/about-aws/whats-new/recent/feed/,https://aws.amazon.com/blogs/security/feed/,https://aws.amazon.com/blogs/compute/feed/,https://aws.amazon.com/blogs/database/feed/"
    local schedule_expression="cron(0 9 * * ? *)"
    local timezone="Europe/Rome"
    local bucket_name=""
    local create_bucket="true"
    local dry_run="false"
    local cleanup_mode="false"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--stack-name)
                stack_name="$2"
                shift 2
                ;;
            -r|--region)
                region="$2"
                shift 2
                ;;
            -b|--bot-name)
                bot_name="$2"
                shift 2
                ;;
            -t|--telegram-token)
                telegram_token="$2"
                shift 2
                ;;
            -c|--chat-id)
                chat_id="$2"
                shift 2
                ;;
            -f|--feeds)
                feed_urls="$2"
                shift 2
                ;;
            --schedule)
                schedule_expression="$2"
                shift 2
                ;;
            --timezone)
                timezone="$2"
                shift 2
                ;;
            --bucket)
                bucket_name="$2"
                shift 2
                ;;
            --no-create-bucket)
                create_bucket="false"
                shift
                ;;
            --cleanup)
                cleanup_mode="true"
                shift
                ;;
            --dry-run)
                dry_run="true"
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Export DRY_RUN for use in functions
    export DRY_RUN="$dry_run"
    
    # Generate bucket name if not provided
    if [[ -z "$bucket_name" ]]; then
        local account_id=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "unknown")
        bucket_name="$bot_name-artifacts-$account_id-$region"
    fi
    
    # Handle cleanup mode
    if [[ "$cleanup_mode" == "true" ]]; then
        print_header "Cleanup Mode"
        echo "Stack Name: $stack_name"
        echo "Region: $region"
        echo "Bot Name: $bot_name"
        echo "S3 Bucket: $bucket_name"
        echo "Dry Run: $dry_run"
        
        if [[ "$dry_run" == "false" ]]; then
            echo -e "\n${YELLOW}WARNING: This will delete ALL AWS resources created by this bot!${NC}"
            echo -e "${YELLOW}Press Enter to continue or Ctrl+C to cancel...${NC}"
            read -r
        fi
        
        cleanup_aws_resources "$stack_name" "$region" "$bot_name" "$bucket_name"
        return 0
    fi
    
    # Validate required parameters for deployment
    if [[ -z "$telegram_token" ]]; then
        print_error "Telegram bot token is required. Use --telegram-token option."
        show_usage
        exit 1
    fi
    
    if [[ -z "$chat_id" ]]; then
        print_error "Telegram chat ID is required. Use --chat-id option."
        show_usage
        exit 1
    fi
    
    # Show deployment configuration
    print_header "Deployment Configuration"
    echo "Stack Name: $stack_name"
    echo "Region: $region"
    echo "Bot Name: $bot_name"
    echo "Chat ID: $chat_id"
    echo "Feed URLs: $feed_urls"
    echo "Schedule: $schedule_expression ($timezone)"
    echo "S3 Bucket: $bucket_name"
    echo "Dry Run: $dry_run"
    
    if [[ "$dry_run" == "false" ]]; then
        echo -e "\n${YELLOW}Press Enter to continue or Ctrl+C to cancel...${NC}"
        read -r
    fi
    
    # Generate unique secret name with timestamp to avoid 7-day deletion restriction
    local timestamp=$(date +%s)
    local secret_name="$bot_name-telegram-token-$timestamp"
    
    # Execute deployment steps
    check_prerequisites
    
    if [[ "$create_bucket" == "true" ]]; then
        create_s3_bucket "$bucket_name" "$region"
    fi
    
    build_lambda_package
    upload_lambda_package "$bucket_name" "$region"
    
    manage_telegram_secret "$secret_name" "$telegram_token" "$region"
    
    deploy_cloudformation "$stack_name" "$region" "$bot_name" "$telegram_token" "$chat_id" "$feed_urls" "$schedule_expression" "$timezone" "$LAMBDA_S3_URI" "$secret_name"
    
    show_deployment_results "$stack_name" "$region"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi