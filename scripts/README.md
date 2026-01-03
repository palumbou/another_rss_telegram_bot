# Scripts Directory

> **Available languages**: [English (current)](README.md) | [Italiano](README.it.md)

This directory contains automation scripts for the Another RSS Telegram Bot project.

## deploy.sh

Automated deployment script for AWS that manages the entire CI/CD pipeline deployment process.

### Features

The script automates the following steps:

1. **Prerequisites Check**: Verifies AWS CLI, Python 3, and zip are installed
2. **S3 Bucket Creation**: Creates artifact bucket (if needed)
3. **Pipeline Deployment**: Deploys CodePipeline infrastructure
4. **Source Packaging**: Creates source code package
5. **S3 Upload**: Uploads source to S3, triggering the pipeline
6. **Automatic Build**: CodeBuild packages the Lambda function
7. **Automatic Deploy**: CloudFormation deploys the application

### Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.12 or higher
- `zip` command available
- Internet connection

### Basic Usage

```bash
# Initial deployment (creates pipeline and deploys application)
./scripts/deploy.sh \
  --telegram-token "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" \
  --chat-id "-1001234567890"
```

### Update Code

```bash
# Update code only (triggers pipeline)
./scripts/deploy.sh --update-code
```

### Available Options

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `--stack-name` | Pipeline stack name | `another-rss-telegram-bot-pipeline` | No |
| `--app-stack` | Application stack name | `another-rss-telegram-bot-app` | No |
| `--region` | AWS region | `us-east-1` | No |
| `--bot-name` | Bot name for resources | `another-rss-telegram-bot` | No |
| `--telegram-token` | Telegram bot token | - | **Yes** (initial) |
| `--chat-id` | Telegram chat ID | - | **Yes** (initial) |
| `--feeds` | RSS feed URLs (comma-separated) | AWS feeds | No |
| `--bucket` | S3 bucket name | Auto-generated | No |
| `--update-code` | Update code only | false | No |
| `--cleanup` | Delete all resources | false | No |
| `--dry-run` | Simulate without executing | false | No |
| `--help` | Show help | - | No |

### Usage Examples

#### 1. Initial Deployment
```bash
./scripts/deploy.sh \
  --telegram-token "YOUR_TOKEN" \
  --chat-id "YOUR_CHAT_ID" \
  --region "eu-west-1"
```

#### 2. Update Code
```bash
./scripts/deploy.sh --update-code --region "eu-west-1"
```

#### 3. Custom Feeds
```bash
./scripts/deploy.sh \
  --telegram-token "YOUR_TOKEN" \
  --chat-id "YOUR_CHAT_ID" \
  --feeds "https://example.com/feed1.xml,https://example.com/feed2.xml"
```

#### 4. Dry Run
```bash
./scripts/deploy.sh \
  --telegram-token "YOUR_TOKEN" \
  --chat-id "YOUR_CHAT_ID" \
  --dry-run
```

#### 5. Cleanup
```bash
./scripts/deploy.sh --cleanup --region "eu-west-1"
```

### How to Get Required Parameters

#### Telegram Bot Token
1. Contact [@BotFather](https://t.me/botfather) on Telegram
2. Use `/newbot` command to create a new bot
3. Follow instructions to choose name and username
4. Copy the provided token (format: `123456:ABC-DEF...`)

#### Telegram Chat ID
1. Add the bot to your channel/group
2. Send a message in the channel/group
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find the `"chat":{"id":...}` field in the response
5. Use the ID found (channels start with `-100`)

### Deployment Workflow

#### Initial Deployment
1. Script creates S3 bucket for artifacts
2. Deploys CodePipeline infrastructure stack
3. Packages source code into zip
4. Uploads source to S3 (`source/source.zip`)
5. S3 event triggers CodePipeline
6. CodeBuild builds Lambda package
7. CloudFormation deploys application

#### Code Updates
1. Script packages updated source code
2. Uploads to S3 (`source/source.zip`)
3. S3 event triggers CodePipeline
4. Pipeline rebuilds and redeploys automatically

### Output

The script provides detailed information during execution:

- ✅ **Prerequisites checks**: Dependency verification
- 📦 **Source packaging**: Creating source archive
- ☁️ **S3 upload**: Uploading artifacts
- 🚀 **Pipeline deployment**: Infrastructure setup
- 📊 **Results**: Links for monitoring

### Troubleshooting

#### Common Issues

1. **AWS credentials not configured**
   ```bash
   aws configure
   # Enter Access Key ID, Secret Access Key, and region
   ```

2. **Bucket already exists**
   - Use `--bucket` with a different name
   - Or delete the existing bucket first

3. **Pipeline not triggering**
   - Check S3 event notification is configured
   - Verify EventBridge rule is enabled
   - Check CloudWatch logs for errors

4. **Stack update failed**
   - Check CloudFormation events in AWS Console
   - Verify parameters are correct
   - Use `--dry-run` to test configuration

### Monitoring

After deployment, monitor the bot via:

- **CodePipeline Console**: Check pipeline execution status
- **CloudWatch Logs**: `/aws/lambda/{bot-name}-processor`
- **CloudWatch Dashboard**: `{bot-name}-monitoring`
- **AWS Console**: Links provided in script output

### Security

The script implements security best practices:

- 🔐 Telegram token stored in AWS Secrets Manager
- 🛡️ S3 bucket with server-side encryption
- 🔒 Versioning enabled for artifacts
- 👤 Least privilege IAM roles

### Customization

To modify script behavior:

1. **Default feeds**: Edit `feed_urls` variable
2. **Bucket naming**: Modify bucket name generation logic
3. **Stack names**: Change default stack name constants

---

*This script is part of the Kiro AI experiment for deployment automation*
