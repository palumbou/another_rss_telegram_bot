# Infrastructure Guide

> **Available languages**: [English (current)](INFRASTRUCTURE.md) | [Italiano](INFRASTRUCTURE.it.md)

## Overview

This document describes the complete AWS infrastructure for the Another RSS Telegram Bot, including the CI/CD pipeline with CodePipeline.

## Architecture Diagram

```
┌──────────────────────────────────────────────────┐
│              Deploy Script                       │
│         (uploads source to S3)                   │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│           S3 Artifact Bucket                     │
│         (source/source.zip)                      │
└──────────────────┬───────────────────────────────┘
                   │ (S3 event trigger)
                   ▼
┌───────────────────────────────────────────────────┐
│           AWS CodePipeline                        │
├───────────────────────────────────────────────────┤
│  Source Stage  →  Build Stage  →  Deploy Stage    │
│     (S3)          (CodeBuild)     (CloudFormation)│
└──────────────────────┬────────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────────┐
│         Application Infrastructure                │
├───────────────────────────────────────────────────┤
│  EventBridge  →  Lambda  →  DynamoDB              │
│                    ↓                              │
│              Bedrock + Telegram                   │
│                    ↓                              │
│              CloudWatch + SQS DLQ                 │
└───────────────────────────────────────────────────┘
```

## Components

### CI/CD Pipeline

#### 1. S3 Artifact Bucket
- **Purpose**: Stores pipeline artifacts and Lambda deployment packages
- **Features**:
  - Versioning enabled
  - Server-side encryption (AES256)
  - Lifecycle policies for cleanup
- **Naming**: `{bot-name}-artifacts-{account-id}-{region}`

#### 2. CodePipeline
- **Stages**:
  1. **Source**: Pulls code from GitHub repository
  2. **Build**: Packages Lambda function with dependencies
  3. **Deploy**: Updates CloudFormation stack

#### 3. CodeBuild Project
- **Runtime**: Python 3.12
- **Build Process**:
  1. Install dependencies from `requirements.txt`
  2. Package source code
  3. Create deployment artifact
  4. Upload to S3
- **Build Spec**: Defined in `buildspec.yml`

### Application Infrastructure

#### 1. Lambda Function
- **Runtime**: Python 3.12
- **Memory**: 512 MB (configurable)
- **Timeout**: 300 seconds (configurable)
- **Trigger**: EventBridge Scheduler (daily)
- **Code Source**: S3 bucket (updated by pipeline)

#### 2. DynamoDB Table
- **Purpose**: Deduplication storage
- **Key**: `item_id` (String)
- **TTL**: 90 days (configurable)
- **Billing**: Pay-per-request

#### 3. EventBridge Scheduler
- **Default Schedule**: Daily at 9:00 AM
- **Timezone**: Europe/Rome (configurable)
- **Target**: Lambda function

#### 4. Secrets Manager
- **Secret**: Telegram bot token
- **Access**: Lambda function only
- **Rotation**: Manual (can be automated)

#### 5. SQS Dead Letter Queue
- **Purpose**: Failed execution handling
- **Retention**: 14 days
- **Visibility Timeout**: 60 seconds

#### 6. CloudWatch
- **Log Group**: `/aws/lambda/{bot-name}-processor`
- **Retention**: 30 days (configurable)
- **Dashboard**: Custom monitoring dashboard
- **Metrics**: Custom application metrics

## Deployment

### Initial Setup

1. **Prepare CloudFormation Parameters**
   ```yaml
   BotName: another-rss-telegram-bot
   TelegramBotToken: "YOUR_BOT_TOKEN"
   TelegramChatId: "YOUR_CHAT_ID"
   RSSFeedUrls: "https://aws.amazon.com/blogs/aws/feed/,..."
   ```

2. **Deploy Pipeline Stack**
   ```bash
   ./scripts/deploy.sh \
     --telegram-token "YOUR_BOT_TOKEN" \
     --chat-id "YOUR_CHAT_ID" \
     --region eu-west-1
   ```

   This will:
   - Create S3 bucket for artifacts
   - Deploy CodePipeline infrastructure
   - Package and upload source code
   - Trigger automatic build and deployment

### Automated Updates

Once the pipeline is set up:

1. **Update Code**: Make changes to your code
2. **Deploy Update**:
   ```bash
   ./scripts/deploy.sh --update-code --region eu-west-1
   ```
3. **Automatic Process**: 
   - Script packages and uploads source to S3
   - S3 event triggers CodePipeline
   - CodeBuild packages the application
   - CloudFormation updates the stack
4. **Verification**: Check CloudWatch logs for successful deployment

### Manual Deployment

For testing or emergency updates:

```bash
# Build locally
python3 -m pip install -r requirements.txt -t build/
cp -r src build/
cd build && zip -r ../lambda.zip . && cd ..

# Upload to S3
aws s3 cp lambda.zip s3://{bucket-name}/lambda-packages/

# Update Lambda function
aws lambda update-function-code \
  --function-name {bot-name}-processor \
  --s3-bucket {bucket-name} \
  --s3-key lambda-packages/lambda.zip
```

## Configuration

### Environment Variables

The Lambda function uses these environment variables (managed by CloudFormation):

- `TELEGRAM_SECRET_NAME`: Secrets Manager secret name
- `TELEGRAM_CHAT_ID`: Target chat/channel ID
- `DYNAMODB_TABLE`: DynamoDB table name
- `RSS_FEED_URLS`: Comma-separated feed URLs
- `CURRENT_AWS_REGION`: AWS region
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)

### CloudFormation Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `BotName` | Resource naming prefix | `another-rss-telegram-bot` |
| `TelegramBotToken` | Bot token (stored in Secrets Manager) | Required |
| `TelegramChatId` | Target chat ID | Required |
| `RSSFeedUrls` | Comma-separated feed URLs | AWS feeds |
| `ScheduleExpression` | Cron expression | `cron(0 9 * * ? *)` |
| `ScheduleTimezone` | Timezone | `Europe/Rome` |

## Monitoring

### CloudWatch Dashboard

Access the dashboard at:
```
https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name={bot-name}-monitoring
```

**Widgets**:
- Execution success/failure rates
- Processing metrics (feeds, items, messages)
- Error counts and deduplication stats
- Recent error logs

### Custom Metrics

The application publishes these metrics to CloudWatch:

- `ExecutionSuccess` / `ExecutionFailure`
- `FeedsProcessed`
- `ItemsFound`
- `ItemsSummarized`
- `MessagesSent`
- `ItemsDeduplicated`
- `Errors`

### Alarms

Consider setting up CloudWatch Alarms for:
- Lambda execution failures
- DLQ message count
- Error rate threshold
- Lambda duration approaching timeout

## Security

### IAM Roles

#### Lambda Execution Role
- **DynamoDB**: GetItem, PutItem on dedup table
- **Secrets Manager**: GetSecretValue for bot token
- **Bedrock**: InvokeModel for summaries
- **CloudWatch**: PutMetricData, CreateLogStream, PutLogEvents
- **SQS**: SendMessage to DLQ

#### CodeBuild Service Role
- **S3**: GetObject, PutObject on artifact bucket
- **CloudWatch**: CreateLogGroup, CreateLogStream, PutLogEvents
- **ECR**: Pull base images (if needed)

#### CodePipeline Service Role
- **S3**: GetObject, PutObject on artifact bucket
- **CodeBuild**: StartBuild, BatchGetBuilds
- **CloudFormation**: CreateStack, UpdateStack, DescribeStacks
- **IAM**: PassRole for CloudFormation

### Best Practices

1. **Secrets**: Never commit tokens or credentials
2. **Least Privilege**: IAM roles have minimal required permissions
3. **Encryption**: S3 buckets use server-side encryption
4. **Logging**: No sensitive data in CloudWatch logs
5. **Network**: Lambda runs in AWS-managed VPC (no custom VPC needed)

## Cost Optimization

### Estimated Monthly Costs

For daily execution (30 runs/month):

- **Lambda**: ~$0.20 (128MB, 30s avg execution)
- **DynamoDB**: ~$0.25 (on-demand, low traffic)
- **EventBridge**: $0.00 (free tier)
- **Secrets Manager**: $0.40 (1 secret)
- **CloudWatch**: ~$0.50 (logs + metrics)
- **CodePipeline**: $1.00 (1 active pipeline)
- **CodeBuild**: ~$0.10 (30 builds, 1 min each)
- **S3**: ~$0.10 (artifact storage)

**Total**: ~$2.55/month

### Cost Reduction Tips

1. Reduce Lambda memory if possible
2. Adjust log retention period
3. Use S3 lifecycle policies for old artifacts
4. Consider reserved capacity for DynamoDB if traffic increases
5. Disable CodePipeline if manual deployments are sufficient

## Troubleshooting

### Pipeline Failures

**Source Stage**:
- Verify GitHub connection is active
- Check repository and branch names
- Ensure webhook is configured

**Build Stage**:
- Review CodeBuild logs in CloudWatch
- Verify `buildspec.yml` syntax
- Check Python dependencies compatibility

**Deploy Stage**:
- Review CloudFormation events
- Check IAM permissions
- Verify parameter values

### Lambda Execution Failures

1. **Check CloudWatch Logs**:
   ```bash
   aws logs tail /aws/lambda/{bot-name}-processor --follow
   ```

2. **Check DLQ Messages**:
   ```bash
   aws sqs receive-message \
     --queue-url {dlq-url} \
     --max-number-of-messages 10
   ```

3. **Test Manually**:
   ```bash
   aws lambda invoke \
     --function-name {bot-name}-processor \
     --payload '{}' \
     response.json
   ```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| AccessDenied to Bedrock | Region not enabled | Enable Bedrock in region or use fallback |
| Telegram API timeout | Network issues | Check retry logic, increase timeout |
| DynamoDB throttling | High traffic | Switch to provisioned capacity |
| Lambda timeout | Slow feeds | Increase timeout, optimize code |

## Maintenance

### Regular Tasks

- **Weekly**: Review CloudWatch logs for errors
- **Monthly**: Check DLQ for failed messages
- **Quarterly**: Review and update dependencies
- **Yearly**: Rotate Telegram bot token

### Updates

1. **Code Changes**: Push to GitHub (automatic deployment)
2. **Infrastructure Changes**: Update CloudFormation template
3. **Configuration Changes**: Update stack parameters
4. **Dependency Updates**: Update `requirements.txt` and push

## Cleanup

To remove all resources:

```bash
# Delete application stack
aws cloudformation delete-stack \
  --stack-name {stack-name}

# Delete pipeline stack
aws cloudformation delete-stack \
  --stack-name rss-bot-pipeline

# Empty and delete S3 bucket
aws s3 rm s3://{bucket-name} --recursive
aws s3 rb s3://{bucket-name}

# Delete secrets (with recovery window)
aws secretsmanager delete-secret \
  --secret-id {secret-name} \
  --recovery-window-in-days 7
```