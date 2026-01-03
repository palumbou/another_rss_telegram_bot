# Another RSS Telegram Bot

A generic, reusable serverless bot that monitors RSS feeds and sends automatic updates to configured Telegram channels.

> **Available languages**: [English (current)](README.md) | [Italiano](README.IT.md)

## Overview

This project is a **Kiro AI experiment** exploring AI-assisted development from requirements specification to implementation and testing. The system is completely generic and deployable to AWS with infrastructure automation.

### Key Features

- **RSS Monitoring**: Periodic checking of configurable RSS feeds
- **Deduplication**: Prevents duplicate content using DynamoDB
- **AI Summaries**: Generates Italian summaries using Amazon Bedrock with fallback
- **Telegram Integration**: Automatic formatted message delivery
- **Error Handling**: Robust error management with Dead Letter Queue
- **Structured Logging**: Complete logging system for debugging
- **Monitoring**: CloudWatch dashboard and custom metrics

## Architecture

Serverless system on AWS with the following components:

### AWS Components
- **Lambda Function**: Main processing logic (Python 3.12)
- **DynamoDB**: Deduplication storage with 90-day TTL
- **EventBridge Scheduler**: Daily scheduled execution
- **Secrets Manager**: Secure Telegram token storage
- **Amazon Bedrock**: AI summary generation with Claude 3 Haiku
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

The system uses AWS CodePipeline for automated deployment. See [docs/INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md) for complete setup instructions.

## Configuration

### Default RSS Feeds

The system includes these AWS feeds by default:
- AWS Blog: `https://aws.amazon.com/blogs/aws/feed/`
- AWS What's New: `https://aws.amazon.com/about-aws/whats-new/recent/feed/`
- AWS Security Blog: `https://aws.amazon.com/blogs/security/feed/`
- AWS Compute Blog: `https://aws.amazon.com/blogs/compute/feed/`
- AWS Database Blog: `https://aws.amazon.com/blogs/database/feed/`

### Customization

You can completely replace feeds using CloudFormation parameters. See documentation for details.

## Documentation

- [Infrastructure Guide](docs/INFRASTRUCTURE.md) - Complete infrastructure setup
- [Kiro Development Process](docs/kiro-prompt.md) - AI-assisted development methodology
- [Prompts](prompts/README.md) - AI prompt templates

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
