# Another RSS Telegram Bot

A generic, reusable serverless bot that monitors RSS feeds and sends automatic updates to configured Telegram channels.

> **Available languages**: [English (current)](README.md) | [Italiano](README.IT.md)

## Overview

This project is a **Kiro AI experiment** exploring AI-assisted development from requirements specification to implementation and testing. The system is completely generic and deployable to AWS with infrastructure automation.

### Key Features

- **RSS Monitoring**: Periodic checking of configurable RSS feeds
- **24-Hour Filter**: Processes only items published in the last 24 hours
- **Deduplication**: Prevents duplicate content using DynamoDB
- **AI Summaries**: Generates Italian summaries using Amazon Bedrock Nova Micro with fallback
- **Telegram Integration**: Automatic formatted message delivery
- **Error Handling**: Robust error management with Dead Letter Queue
- **Structured Logging**: Complete logging system for debugging
- **Monitoring**: CloudWatch dashboard and custom metrics
- **CI/CD Pipeline**: Automated deployment with AWS CodePipeline and S3

### AI Model

The bot uses **Amazon Nova Micro** (`eu.amazon.nova-micro-v1:0`) for generating Italian summaries. This model was chosen because:
- Cost-effective for high-volume summarization
- Fast response times (< 1 second per summary)
- Good quality Italian translations
- Available via cross-region inference profile in EU

**To use a different model**, you need to modify `src/summarize.py` to match the model's API format. See the [Customization](#customization) section below.

### Example Output

Here's what the bot's messages look like in Telegram:

![Telegram Messages Example](docs/images/telegram-messages-example.png)

Each message includes:
- A concise Italian title
- Three bullet points with key information
- A "Perché conta:" section explaining relevance
- Source link to the original article

## Architecture

Serverless system on AWS with the following components:

### AWS Components
- **Lambda Function**: Main processing logic (Python 3.12)
- **DynamoDB**: Deduplication storage with 90-day TTL
- **EventBridge Scheduler**: Daily scheduled execution
- **Secrets Manager**: Secure Telegram token storage
- **Amazon Bedrock**: AI summary generation with Nova Micro model
- **SQS Dead Letter Queue**: Error handling and retry
- **CloudWatch**: Logging, metrics, and monitoring dashboard
- **CodePipeline**: Automated build and deployment (CI/CD)
- **S3**: Artifact storage and pipeline automation

### Code Components
- `src/lambda_handler.py`: Main entry point and orchestration
- `src/rss.py`: RSS feed management with feedparser
- `src/telegram.py`: Telegram Bot API integration
- `src/summarize.py`: Summary generation with Bedrock and fallback
- `src/dedup.py`: DynamoDB deduplication system
- `src/config.py`: Configuration and environment management
- `src/models.py`: Data models and structures

## Quick Start

### Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.12 or compatible
- Bot created via Telegram @BotFather
- GitHub repository (for CodePipeline integration)

### Deployment

The system uses a unified CloudFormation stack with AWS CodePipeline for automated deployment. A single stack contains all resources (Lambda, DynamoDB, EventBridge, CodePipeline, CodeBuild, etc.). See [docs/INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md) for complete setup instructions.

## Configuration

### RSS Feeds

The bot reads RSS feeds from a `feeds.json` file. You can customize which feeds to monitor by editing this file or providing your own.

**Default feeds** include AWS-related content. See [FEEDS.md](FEEDS.md) for complete documentation on:
- Feed file format
- How to customize feeds
- Examples for different use cases

### Default RSS Feeds

The default `feeds.json` includes these AWS feeds:
- AWS Blog: `https://aws.amazon.com/blogs/aws/feed/`
- AWS What's New: `https://aws.amazon.com/about-aws/whats-new/recent/feed/`
- AWS Security Blog: `https://aws.amazon.com/blogs/security/feed/`
- AWS Compute Blog: `https://aws.amazon.com/blogs/compute/feed/`
- AWS Database Blog: `https://aws.amazon.com/blogs/database/feed/`

### Customization

You can customize feeds by:
1. Editing the `feeds.json` file in the project root
2. Providing a custom feeds file during deployment

See [FEEDS.md](FEEDS.md) for detailed instructions and examples.

## Quick Start

### Prerequisites

- **AWS Account**: Active AWS account with appropriate permissions
- **AWS CLI**: Installed and configured with your credentials
  ```bash
  # Configure AWS CLI with your credentials
  aws configure
  # Or use AWS_PROFILE environment variable
  export AWS_PROFILE=your-profile-name
  ```
- **Python 3.12** or compatible
- **Bot created** via Telegram @BotFather
- **Bedrock Access**: Ensure you have access to Amazon Bedrock models in your region

### Deployment

```bash
# Initial deployment with default feeds
./scripts/deploy.sh \
  --telegram-token "YOUR_BOT_TOKEN" \
  --chat-id "YOUR_CHAT_ID"

# Or with custom feeds file
./scripts/deploy.sh \
  --telegram-token "YOUR_BOT_TOKEN" \
  --chat-id "YOUR_CHAT_ID" \
  --feeds-file /path/to/my-feeds.json

# Skip confirmation prompts
./scripts/deploy.sh \
  --telegram-token "YOUR_BOT_TOKEN" \
  --chat-id "YOUR_CHAT_ID" \
  --yes
```

For complete deployment instructions, see [docs/INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md).

## Customization

### Changing the AI Model

The bot is configured to use Amazon Nova Micro. To use a different Bedrock model:

1. **Update the model ID** in `infrastructure/pipeline-template.yaml`:
   ```yaml
   BEDROCK_MODEL_ID: 'your-model-id-here'
   ```

2. **Modify the API format** in `src/summarize.py` in the `bedrock_summarize()` method:
   - Different models use different request/response formats
   - Consult the [AWS Bedrock documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html) for your model's format
   - Update the `request_body` structure
   - Update the response parsing logic

3. **Example for Claude models**:
   ```python
   request_body = {
       "anthropic_version": "bedrock-2023-05-31",
       "messages": [{"role": "user", "content": prompt}],
       "max_tokens": self.config.max_tokens,
       "temperature": 0.3
   }
   # Response: response_body["content"][0]["text"]
   ```

4. **Redeploy** the application:
   ```bash
   ./scripts/deploy.sh --update-code --region eu-west-1
   ```

## Documentation

- [RSS Feeds Configuration](FEEDS.md) - How to configure and customize RSS feeds
- [Infrastructure Guide](docs/INFRASTRUCTURE.md) - Complete infrastructure setup
- [Kiro Development Process](docs/KIRO-PROMPT.md) - AI-assisted development methodology
- [Prompts](prompts/README.md) - AI prompt templates
- [Deployment Scripts](scripts/README.md) - Deployment automation documentation

## Development Methodology

This project was developed using **spec-driven development** with Kiro AI:

- ✅ Complete requirements specification using EARS format
- ✅ Architectural design with correctness properties
- ✅ Property-based testing implementation
- ✅ Automated testing with Hypothesis for Python
- ✅ Infrastructure-as-Code with CloudFormation
- ✅ Automated deployment with CodePipeline

## License

This project is released under the MIT License.

---

*Developed as an experiment with Kiro AI Assistant*
