#!/usr/bin/env bash

# Another RSS Telegram Bot - Deployment Script
# Deployment automation with CodePipeline and S3 source
# Supports dual model selection: Nova Micro (cost-optimized) or Llama 3.2 3B (quality-optimized)

set -e  # Exit on any error

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_STACK_NAME="another-rss-telegram-bot-pipeline"
DEFAULT_REGION="us-east-1"
DEFAULT_BOT_NAME="another-rss-telegram-bot"

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INFRASTRUCTURE_DIR="$PROJECT_ROOT/infrastructure"
TEMPLATE_FILE="$INFRASTRUCTURE_DIR/pipeline-template.yaml"
DEFAULT_FEEDS_FILE="$PROJECT_ROOT/feeds.json"

# Deployment artifacts
BUILD_DIR="$PROJECT_ROOT/build"
SOURCE_ZIP="$BUILD_DIR/source.zip"

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

Deploy Another RSS Telegram Bot to AWS using CodePipeline

OPTIONS:
    -s, --stack-name STACK_NAME     CloudFormation stack name (default: $DEFAULT_STACK_NAME)
    -r, --region REGION             AWS region (default: $DEFAULT_REGION)
    -b, --bot-name BOT_NAME         Bot name for resource naming (default: $DEFAULT_BOT_NAME)
    -t, --telegram-token TOKEN      Telegram bot token (required for initial deploy)
    -c, --chat-id CHAT_ID           Telegram chat ID (required for initial deploy)
    -T, --topic-id TOPIC_ID         Telegram forum topic ID (optional, sends messages
                                    to a specific topic of a supergroup with topics enabled;
                                    leave unset to send to the chat or the General topic)
    -f, --feeds-file FILE           Path to feeds.json file (optional, uses default if not provided)
    -m, --model MODEL               AI model selection: nova-micro (default), mistral-large, or llama-3b
    -M, --message-mode MODE         Telegram delivery mode: per_item (default) or digest
    --bucket BUCKET_NAME            S3 bucket for artifacts (optional, auto-generated if not provided)
    --cleanup                       Delete all AWS resources created by this bot
    --update-code                   Update only the source code (trigger pipeline)
    --update-stack                  Update stack parameters (e.g., change model) without redeploying code
    --dry-run                       Show what would be deployed without executing
    -y, --yes                       Skip confirmation prompts
    -h, --help                      Show this help message

PREREQUISITES:
    - AWS CLI installed and configured with credentials
    - AWS credentials configured (run 'aws configure' or set AWS_PROFILE)
    - Python 3.12 or compatible
    - zip command available

EXAMPLES:
    # Initial deployment with default Nova Micro model (cost-optimized)
    $0 --telegram-token "123456:ABC-DEF..." --chat-id "-1001234567890"
    
    # Initial deployment with Llama 3.2 3B model (quality-optimized)
    $0 --telegram-token "123456:ABC-DEF..." --chat-id "-1001234567890" \\
       --model llama-3b
    
    # Initial deployment with Mistral Large (best multilingual translation)
    $0 --telegram-token "123456:ABC-DEF..." --chat-id "-1001234567890" \\
       --model mistral-large
    
    # Initial deployment with custom feeds file and Nova Micro
    $0 --telegram-token "123456:ABC-DEF..." --chat-id "-1001234567890" \\
       --feeds-file /path/to/my-feeds.json --model nova-micro

    # Initial deployment sending messages to a specific forum topic
    $0 --telegram-token "123456:ABC-DEF..." --chat-id "-1001234567890" \\
       --topic-id "13"

    # Move the bot to a forum topic on an existing deployment
    $0 --update-stack --topic-id "13"

    # Update code only (triggers pipeline)
    $0 --update-code
    
    # Update stack parameters (e.g., switch model from nova-micro to llama-3b)
    $0 --update-stack --model llama-3b
    
    # Cleanup all resources
    $0 --cleanup --region "eu-west-1"

MODEL SELECTION:
    nova-micro      Amazon Nova Micro v1:0 (default)
                    - Most cost-effective (~$0.015/month for 150 articles)
                    - Fast inference
                    - Best for high-volume RSS processing
    
    mistral-large   Mistral Large 2 (24.07)
                    - Excellent multilingual translation (EN→IT)
                    - Superior reasoning and context understanding
                    - Best for complex content and accurate translations
                    - Cost: ~$0.78/month for 150 articles
    
    llama-3b        Meta Llama 3.2 3B Instruct
                    - Quality-optimized, better summaries
                    - Good for detailed content analysis
                    - Cost: ~$0.06/month for 150 articles

MESSAGE MODE:
    per_item        One Telegram message per news item (default)

    digest          A single combined message with all the day's news
                    (automatically split into multiple parts if it exceeds
                    Telegram's 4096-character limit)

    NOTE: when using --update-stack, re-specify --message-mode if you use
    a non-default mode, otherwise it will be reset to per_item.

TOPIC ID:
    When --topic-id is set, messages are sent to that topic of a supergroup
    with topics (forum) enabled. The topic ID is the second numeric segment
    of the topic link (e.g. https://t.me/c/1234567890/13 -> topic ID 13).
    The bot must be an administrator of the group with the "Manage Topics"
    permission (can_manage_topics), otherwise the Telegram API returns
    TOPIC_CLOSED on closed topics.

    NOTE: when using --update-stack, re-specify --topic-id if you use one,
    otherwise it will be reset (messages go back to the chat/General topic).

FEEDS FILE FORMAT:
    The feeds.json file should have this structure:
    {
      "feeds": [
        {
          "url": "https://example.com/feed.xml",
          "name": "Example Feed",
          "enabled": true
        }
      ]
    }

WORKFLOW:
    1. Initial deployment creates the CodePipeline infrastructure
    2. Feeds file is validated and included in source package
    3. Source code is packaged and uploaded to S3
    4. Pipeline automatically builds and deploys the application
    5. Subsequent updates only need --update-code flag

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

# Function to validate feeds file
validate_feeds_file() {
    local feeds_file="$1"
    
    print_header "Validating Feeds File"
    
    if [[ ! -f "$feeds_file" ]]; then
        print_error "Feeds file not found: $feeds_file"
        exit 1
    fi
    
    print_status "Checking feeds file: $feeds_file"
    
    # Validate JSON syntax
    if ! python3 -c "import json; json.load(open('$feeds_file'))" 2>/dev/null; then
        print_error "Invalid JSON in feeds file: $feeds_file"
        exit 1
    fi
    
    # Validate structure
    local has_feeds=$(python3 -c "import json; data=json.load(open('$feeds_file')); print('feeds' in data)" 2>/dev/null)
    if [[ "$has_feeds" != "True" ]]; then
        print_error "Feeds file must contain a 'feeds' array"
        exit 1
    fi
    
    # Count enabled feeds
    local feed_count=$(python3 -c "import json; data=json.load(open('$feeds_file')); print(len([f for f in data['feeds'] if f.get('enabled', True)]))" 2>/dev/null)
    
    if [[ "$feed_count" -eq 0 ]]; then
        print_warning "No enabled feeds found in feeds file"
    else
        print_success "Feeds file validated: $feed_count enabled feed(s)"
    fi
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
    
    print_success "S3 bucket '$bucket_name' created successfully (policy will be applied after stack deployment)"
}

# Function to apply bucket policy after IAM roles are created
apply_bucket_policy() {
    local bucket_name="$1"
    local bot_name="$2"
    
    print_header "Applying S3 Bucket Policy"
    
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    
    print_status "Setting bucket policy for CodePipeline and CodeBuild access"
    aws s3api put-bucket-policy \
        --bucket "$bucket_name" \
        --policy "{
            \"Version\": \"2012-10-17\",
            \"Statement\": [
                {
                    \"Sid\": \"AllowCodePipelineServiceRole\",
                    \"Effect\": \"Allow\",
                    \"Principal\": {
                        \"AWS\": \"arn:aws:iam::${account_id}:role/${bot_name}-codepipeline-role\"
                    },
                    \"Action\": [
                        \"s3:GetObject\",
                        \"s3:GetObjectVersion\",
                        \"s3:PutObject\"
                    ],
                    \"Resource\": \"arn:aws:s3:::${bucket_name}/*\"
                },
                {
                    \"Sid\": \"AllowCodePipelineServiceRoleBucket\",
                    \"Effect\": \"Allow\",
                    \"Principal\": {
                        \"AWS\": \"arn:aws:iam::${account_id}:role/${bot_name}-codepipeline-role\"
                    },
                    \"Action\": [
                        \"s3:ListBucket\",
                        \"s3:GetBucketVersioning\",
                        \"s3:GetBucketLocation\"
                    ],
                    \"Resource\": \"arn:aws:s3:::${bucket_name}\"
                },
                {
                    \"Sid\": \"AllowCodeBuildServiceRole\",
                    \"Effect\": \"Allow\",
                    \"Principal\": {
                        \"AWS\": \"arn:aws:iam::${account_id}:role/${bot_name}-codebuild-role\"
                    },
                    \"Action\": [
                        \"s3:GetObject\",
                        \"s3:PutObject\"
                    ],
                    \"Resource\": \"arn:aws:s3:::${bucket_name}/*\"
                },
                {
                    \"Sid\": \"AllowCodeBuildServiceRoleBucket\",
                    \"Effect\": \"Allow\",
                    \"Principal\": {
                        \"AWS\": \"arn:aws:iam::${account_id}:role/${bot_name}-codebuild-role\"
                    },
                    \"Action\": [
                        \"s3:ListBucket\",
                        \"s3:GetBucketLocation\"
                    ],
                    \"Resource\": \"arn:aws:s3:::${bucket_name}\"
                }
            ]
        }"
    
    print_success "Bucket policy applied successfully"
}

# Function to create source package
create_source_package() {
    local feeds_file="$1"
    
    print_header "Creating Source Package"
    
    print_status "Preparing build directory"
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "[DRY RUN] Would create source package: $SOURCE_ZIP"
        print_status "[DRY RUN] Would include feeds file: $feeds_file"
        return 0
    fi
    
    print_status "Creating source archive"
    cd "$PROJECT_ROOT"
    
    # Create zip with all source files including feeds and prompts
    # Exclude README files from prompts as they're only documentation
    zip -r "$SOURCE_ZIP" \
        src/ \
        infrastructure/ \
        requirements.txt \
        buildspec.yml \
        -x "*.pyc" "*__pycache__*" "*.git*" \
        -q
    
    # Add prompts directory but exclude README files
    zip -r "$SOURCE_ZIP" prompts/ \
        -x "prompts/README.md" "prompts/README.it.md" \
        -q
    
    # Add feeds file to the zip
    print_status "Adding feeds file to package"
    zip -j "$SOURCE_ZIP" "$feeds_file" -q
    
    local zip_size=$(du -h "$SOURCE_ZIP" | cut -f1)
    print_success "Source package created: $SOURCE_ZIP ($zip_size)"
}

# Function to upload source to S3 and trigger pipeline
upload_source_and_trigger() {
    local bucket_name="$1"
    local region="$2"
    local pipeline_name="$3"
    
    local s3_key="source/source.zip"
    local s3_uri="s3://$bucket_name/$s3_key"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_header "Uploading Source to S3"
        print_status "[DRY RUN] Would upload source to: $s3_uri"
        print_status "[DRY RUN] Would trigger pipeline: $pipeline_name"
        return 0
    fi
    
    print_header "Uploading Source to S3"
    print_status "Uploading to: $s3_uri"
    
    aws s3 cp "$SOURCE_ZIP" "$s3_uri" --region "$region"
    
    print_success "Source uploaded successfully"
    
    # Trigger pipeline manually since EventBridge auto-trigger is disabled
    print_status "Triggering CodePipeline manually..."
    aws codepipeline start-pipeline-execution \
        --name "$pipeline_name" \
        --region "$region" \
        --output json > /dev/null
    
    print_success "Pipeline execution started"
}

# Function to deploy pipeline stack
deploy_pipeline_stack() {
    local stack_name="$1"
    local region="$2"
    local bot_name="$3"
    local telegram_token="$4"
    local chat_id="$5"
    local bucket_name="$6"
    local model_selection="$7"
    local message_mode="$8"
    local topic_id="$9"

    print_header "Deploying Pipeline Stack"

    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "[DRY RUN] Would deploy stack: $stack_name"
        print_status "Parameters:"
        print_status "  BotName: $bot_name"
        print_status "  TelegramChatId: $chat_id"
        print_status "  TelegramTopicId: ${topic_id:-<none>}"
        print_status "  ArtifactBucketName: $bucket_name"
        print_status "  BedrockModelSelection: $model_selection"
        print_status "  MessageMode: $message_mode"
        return 0
    fi

    print_status "Deploying stack: $stack_name"
    print_status "Template: $TEMPLATE_FILE"
    print_status "Region: $region"
    print_status "Model Selection: $model_selection"
    print_status "Message Mode: $message_mode"
    if [[ -n "$topic_id" ]]; then
        print_status "Topic ID: $topic_id"
    fi

    # Build parameter overrides
    local params="BotName=$bot_name TelegramBotToken=$telegram_token TelegramChatId=$chat_id TelegramTopicId=$topic_id ArtifactBucketName=$bucket_name BedrockModelSelection=$model_selection MessageMode=$message_mode"
    
    aws cloudformation deploy \
        --template-file "$TEMPLATE_FILE" \
        --stack-name "$stack_name" \
        --parameter-overrides $params \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$region" \
        --no-fail-on-empty-changeset
    
    print_success "Stack deployed successfully"
}

# Function to get bucket name from stack
get_artifact_bucket() {
    local stack_name="$1"
    local region="$2"
    
    local bucket=$(aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$region" \
        --query 'Stacks[0].Outputs[?OutputKey==`ArtifactBucketName`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    echo "$bucket"
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
    local topic_id=""
    local feeds_file="$DEFAULT_FEEDS_FILE"
    local bucket_name=""
    local model_selection="nova-micro"
    local message_mode="per_item"
    local dry_run="false"
    local cleanup_mode="false"
    local update_code_only="false"
    local update_stack_only="false"
    local skip_confirmation="false"
    
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
            -T|--topic-id)
                topic_id="$2"
                # Validate topic ID (must be numeric)
                if [[ ! "$topic_id" =~ ^[0-9]+$ ]]; then
                    print_error "Invalid topic ID: $topic_id"
                    print_error "Topic ID must be a positive integer (e.g. 13)"
                    exit 1
                fi
                shift 2
                ;;
            -f|--feeds-file)
                feeds_file="$2"
                shift 2
                ;;
            -m|--model)
                model_selection="$2"
                # Validate model selection
                if [[ "$model_selection" != "nova-micro" && "$model_selection" != "mistral-large" && "$model_selection" != "llama-3b" ]]; then
                    print_error "Invalid model selection: $model_selection"
                    print_error "Valid options are: nova-micro, mistral-large, llama-3b"
                    exit 1
                fi
                shift 2
                ;;
            -M|--message-mode)
                message_mode="$2"
                # Validate message mode
                if [[ "$message_mode" != "per_item" && "$message_mode" != "digest" ]]; then
                    print_error "Invalid message mode: $message_mode"
                    print_error "Valid options are: per_item, digest"
                    exit 1
                fi
                shift 2
                ;;
            --bucket)
                bucket_name="$2"
                shift 2
                ;;
            --cleanup)
                cleanup_mode="true"
                shift
                ;;
            --update-code)
                update_code_only="true"
                shift
                ;;
            --update-stack)
                update_stack_only="true"
                shift
                ;;
            --dry-run)
                dry_run="true"
                shift
                ;;
            -y|--yes)
                skip_confirmation="true"
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
        bucket_name="$bot_name-pipeline-artifacts-$account_id"
    fi
    
    # Handle cleanup mode
    if [[ "$cleanup_mode" == "true" ]]; then
        print_header "Cleanup Mode"
        echo "Stack: $stack_name"
        echo "Region: $region"
        echo "S3 Bucket: $bucket_name"
        
        if [[ "$dry_run" == "false" && "$skip_confirmation" == "false" ]]; then
            echo -e "\n${YELLOW}WARNING: This will delete ALL AWS resources!${NC}"
            echo -e "${YELLOW}Press Enter to continue or Ctrl+C to cancel...${NC}"
            read -r
        fi
        
        cleanup_aws_resources "$stack_name" "$region" "$bot_name" "$bucket_name"
        return 0
    fi
    
    # Handle update code only mode
    if [[ "$update_code_only" == "true" ]]; then
        print_header "Update Code Mode"
        
        # Get bucket from existing stack
        local existing_bucket=$(get_artifact_bucket "$stack_name" "$region")
        if [[ -z "$existing_bucket" ]]; then
            print_error "Could not find artifact bucket. Pipeline stack may not exist."
            print_error "Run initial deployment first without --update-code flag."
            exit 1
        fi
        
        bucket_name="$existing_bucket"
        print_status "Using existing bucket: $bucket_name"
        
        check_prerequisites
        validate_feeds_file "$feeds_file"
        create_source_package "$feeds_file"
        
        # Get the pipeline name
        local pipeline_name="$bot_name-pipeline"
        upload_source_and_trigger "$bucket_name" "$region" "$pipeline_name"
        
        print_success "Code updated! Pipeline will deploy automatically."
        print_status "Monitor pipeline at: https://$region.console.aws.amazon.com/codesuite/codepipeline/pipelines"
        return 0
    fi
    
    # Handle update stack only mode (update parameters without redeploying code)
    if [[ "$update_stack_only" == "true" ]]; then
        print_header "Update Stack Parameters Mode"
        
        # Check if stack exists
        if ! aws cloudformation describe-stacks --stack-name "$stack_name" --region "$region" &>/dev/null; then
            print_error "Stack '$stack_name' not found in region '$region'"
            print_error "Run initial deployment first without --update-stack flag."
            exit 1
        fi
        
        print_status "Updating stack: $stack_name"
        print_status "Region: $region"
        
        if [[ -n "$model_selection" ]]; then
            print_status "Changing model to: $model_selection"
        fi
        print_status "Message mode: $message_mode"
        if [[ -n "$chat_id" ]]; then
            print_status "Changing chat ID to: $chat_id"
        fi
        print_status "Topic ID: ${topic_id:-<none, chat/General topic>}"
        
        if [[ "$dry_run" == "false" && "$skip_confirmation" == "false" ]]; then
            echo -e "\n${YELLOW}This will update the CloudFormation stack parameters.${NC}"
            echo -e "${YELLOW}Press Enter to continue or Ctrl+C to cancel...${NC}"
            read -r
        fi
        
        if [[ "$dry_run" == "true" ]]; then
            print_status "[DRY RUN] Would update stack parameters"
            if [[ -n "$model_selection" ]]; then
                print_status "[DRY RUN] Would set BedrockModelSelection=$model_selection"
            fi
            return 0
        fi
        
        # Build parameters array - use previous values for all except what's specified
        local params="ParameterKey=BotName,UsePreviousValue=true"
        params="$params ParameterKey=TelegramBotToken,UsePreviousValue=true"
        params="$params ParameterKey=ArtifactBucketName,UsePreviousValue=true"
        params="$params ParameterKey=LambdaTimeout,UsePreviousValue=true"
        params="$params ParameterKey=LambdaMemorySize,UsePreviousValue=true"
        params="$params ParameterKey=ScheduleExpression,UsePreviousValue=true"
        params="$params ParameterKey=ScheduleTimezone,UsePreviousValue=true"
        params="$params ParameterKey=DynamoDBTTLDays,UsePreviousValue=true"
        params="$params ParameterKey=LogRetentionDays,UsePreviousValue=true"
        
        # Override chat ID if specified, otherwise keep the current one
        if [[ -n "$chat_id" ]]; then
            params="$params ParameterKey=TelegramChatId,ParameterValue=$chat_id"
        else
            params="$params ParameterKey=TelegramChatId,UsePreviousValue=true"
        fi

        # Override model selection if specified
        if [[ -n "$model_selection" ]]; then
            params="$params ParameterKey=BedrockModelSelection,ParameterValue=$model_selection"
        else
            params="$params ParameterKey=BedrockModelSelection,UsePreviousValue=true"
        fi

        # Message mode always has a value (defaults to per_item)
        params="$params ParameterKey=MessageMode,ParameterValue=$message_mode"

        # Topic ID always passed explicitly: UsePreviousValue=true would fail
        # on stacks created before this parameter existed
        params="$params ParameterKey=TelegramTopicId,ParameterValue=$topic_id"
        
        print_status "Updating CloudFormation stack..."
        aws cloudformation update-stack \
            --stack-name "$stack_name" \
            --template-body "file://$TEMPLATE_FILE" \
            --parameters $params \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$region"
        
        print_status "Waiting for stack update to complete..."
        aws cloudformation wait stack-update-complete \
            --stack-name "$stack_name" \
            --region "$region"
        
        print_success "Stack parameters updated successfully!"
        print_status "Lambda function will use the new configuration on next execution."
        
        if [[ -n "$model_selection" ]]; then
            print_success "Model changed to: $model_selection"
        fi
        
        return 0
    fi
    
    # Initial deployment - validate required parameters
    if [[ -z "$telegram_token" ]]; then
        print_error "Telegram bot token is required for initial deployment. Use --telegram-token option."
        show_usage
        exit 1
    fi
    
    if [[ -z "$chat_id" ]]; then
        print_error "Telegram chat ID is required for initial deployment. Use --chat-id option."
        show_usage
        exit 1
    fi
    
    # Show deployment configuration
    print_header "Initial Deployment Configuration"
    echo "Stack Name: $stack_name"
    echo "Region: $region"
    echo "Bot Name: $bot_name"
    echo "Chat ID: $chat_id"
    echo "Topic ID: ${topic_id:-<none, chat/General topic>}"
    echo "Feeds File: $feeds_file"
    echo "S3 Bucket: $bucket_name"
    echo "Model Selection: $model_selection"
    echo "Message Mode: $message_mode"
    echo "Dry Run: $dry_run"
    
    if [[ "$dry_run" == "false" && "$skip_confirmation" == "false" ]]; then
        echo -e "\n${YELLOW}Press Enter to continue or Ctrl+C to cancel...${NC}"
        read -r
    fi
    
    # Execute deployment steps
    check_prerequisites
    validate_feeds_file "$feeds_file"
    
    # Create S3 bucket first (without policy)
    create_s3_bucket "$bucket_name" "$region"
    
    # Deploy stack (creates IAM roles)
    deploy_pipeline_stack "$stack_name" "$region" "$bot_name" "$telegram_token" "$chat_id" "$bucket_name" "$model_selection" "$message_mode" "$topic_id"
    
    # Apply bucket policy now that IAM roles exist
    apply_bucket_policy "$bucket_name" "$bot_name"
    
    # Create and upload source package
    create_source_package "$feeds_file"
    
    # Get the pipeline name from the stack
    local pipeline_name="$bot_name-pipeline"
    upload_source_and_trigger "$bucket_name" "$region" "$pipeline_name"
    
    print_success "Initial deployment completed!"
    print_status "Pipeline will now build and deploy the application automatically."
    print_status "Monitor at: https://$region.console.aws.amazon.com/codesuite/codepipeline/pipelines"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi