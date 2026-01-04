# Kiro Development Prompt

> **Available languages**: [English (current)](KIRO-PROMPT.md) | [Italiano](KIRO-PROMPT.it.md)

## Original Prompt

This project was developed using Kiro AI assistant following the spec-driven development methodology.

**Note**: The original prompt was written in Italian and has been translated to English for this document. See [KIRO-PROMPT.it.md](KIRO-PROMPT.it.md) for the original Italian version.

**Initial user request:**
```
Act as a senior AWS Serverless Engineer. You must generate a complete, deploy-ready repository for a generic (reusable) Telegram bot that daily reads a list of RSS/Atom feeds and publishes an Italian summary + link to a Telegram channel/group.

NON-NEGOTIABLE REQUIREMENTS
1) Infrastructure as Code: ONLY AWS CloudFormation (YAML or JSON templates). No CDK, no Terraform.
2) Lambda: Python (preferably 3.12).
3) "One command" deploy via BASH SCRIPT: the user should not create anything manually in AWS.
They only need to provide:
- AWS credentials already available in terminal (e.g., AWS_PROFILE or standard AWS env vars)
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID (or target channel/group)
Everything else (artifact bucket, secret, CloudFormation stack) must be created automatically by the script.

PROJECT NAME (IMPORTANT)
- The project name must be GENERIC and reusable, because:
- the RSS feed list can be changed for any source
- the Telegram target can be changed for any channel/group
- Avoid names tied to AWS User Group or "AWS-only". Use neutral naming (e.g., rss-to-telegram-summarizer or similar).

ARCHITECTURE
- EventBridge Scheduler (or EventBridge Rule cron) -> Lambda (Python)
- DynamoDB for deduplication/state with TTL (e.g., 90 days)
- Secrets Manager for TELEGRAM_BOT_TOKEN (created/updated by script)
- CloudWatch Logs + custom metrics
- SQS DLQ for error handling (connected to Lambda)
- S3 artifact bucket to upload Lambda zip (created by script)

FUNCTIONALITY
- Every day (default 09:00, timezone Europe/Rome) the Lambda:
1) reads configurable FEED_URLS (JSON array)
2) downloads RSS/Atom via HTTPS and normalizes items: title, link, published, summary/content (clean HTML)
3) deduplicates:
- uses GUID if present, otherwise SHA256(feedUrl + link + published)
- if already in DynamoDB: skip
- if new: save in DynamoDB with TTL
4) generates Italian summary:
- preference: Amazon Bedrock (boto3 bedrock-runtime) with controlled prompt:
- 1 line title
- 3 bullets in Italian (<= 15 words each)
- final line "Perché conta:" (<= 20 words)
- no inventions: if info missing, be cautious
- VERY IMPORTANT: automatic fallback if Bedrock unavailable or AccessDenied:
- simple and stable extractive summary (without heavy dependencies)
5) sends to Telegram via Bot API sendMessage (HTML parse_mode recommended)
- always include original link
- handles errors (429/timeouts) with retry + backoff

DEFAULT FEED LIST (AWS)
- The project must include a default AWS-oriented feed list (user-modifiable), for example:
- AWS Blog / News Blog (or equivalent available feeds)
- AWS "What's New" (or equivalent feed)
- AWS Security Blog / Security Bulletins (or equivalent feed)
- Any official announcement feeds if available in RSS/Atom
- The list must be set as default in the template (or as default parameter) and documented in README.
- However, the project must remain GENERIC: clearly explain how to replace feeds with any other RSS.

SECURITY / CONFIG
- TELEGRAM_BOT_TOKEN in Secrets Manager (never in clear in repo, never in logs)
- Chat ID/Target and FEED_URLS: as CloudFormation parameters (or SSM), but managed by deploy script (no console clicks)
- IAM least privilege for:
- dynamodb PutItem/GetItem
- secretsmanager GetSecretValue
- logs CreateLogStream/PutLogEvents
- (optional) bedrock:InvokeModel
- Don't log secrets.

CLOUDFORMATION TEMPLATE
- Provide a complete CloudFormation template that creates:
- DynamoDB table with TTL
- Lambda function (code from S3)
- IAM Role + minimal policies
- Daily EventBridge Scheduler/Rule (timezone Europe/Rome)
- SQS DLQ and associated configuration
- LogGroup (optional with retention)
- Useful Outputs (FunctionName, LogGroupName, etc.)

DEPLOY AUTOMATION (BASH SCRIPT)
- The repo must have a "one shot" bash script (e.g., scripts/deploy.sh) that:
1) verifies prerequisites (aws cli, python3, zip)
2) determines account id and region (aws sts get-caller-identity)
3) creates an S3 bucket for artifacts if it doesn't exist (unique name with account+region)
4) builds the Lambda (zip with sources and requirements)
5) uploads zip to S3 and gets S3Key (possible version id)
6) creates/updates secret in Secrets Manager with TELEGRAM_BOT_TOKEN (from env var)
7) executes `aws cloudformation deploy` with parameters:
- TelegramSecretArn
- TelegramChatId
- FeedUrls (JSON)
- Schedule (default daily)
- Timezone (default Europe/Rome)
- BedrockModelId (configurable default)
8) prints stack outputs and indicates where to see logs in CloudWatch

REPO STRUCTURE
- /infra/template.yaml (CloudFormation)
- /src/ (lambda handler + modules: rss.py, dedup.py, summarize.py, telegram.py, config.py)
- /scripts/deploy.sh
- /tests/ (pytest: itemId hash, dedup, HTML telegram formatter)
- /prompts (summary prompt file)
- /docs/kiro-prompt.md (MANDATORY): contains this complete prompt
- README.md:
- explains that the project is GENERIC and reusable (configurable RSS + Telegram)
- lists the included DEFAULT AWS FEED LIST
- explains how to change FEED_URLS to use different sources
- explains how to set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
- provides copy/paste "deploy in less than 5 minutes" instructions:
export AWS_PROFILE=... (optional)
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_CHAT_ID=...
/scripts/deploy.sh
- includes a "Prompt used / Provenance" section that LINKS to /docs/kiro-prompt.md and explains that this is the prompt used to generate the project.
- GitHub Actions: lint + test (ruff + pytest)

EXPECTED OUTPUT
- Generate ALL repo files with complete content.
- Ensure deployment works without AWS console clicks.
```

## Development Process

The project was developed following the Kiro workflow for specification creation:

### 1. Requirements Phase
- Analysis of functional and non-functional requirements
- Definition of acceptance criteria using EARS patterns
- Identification of testable correctness properties

### 2. Design Phase
- Serverless architecture on AWS
- Component and interface definition
- Mapping correctness properties from requirements
- Dual testing strategy (unit + property-based)

### 3. Tasks Phase
- Breakdown into incrementally implementable tasks
- Definition of validation checkpoints
- Marking optional tasks for fast MVP

## Methodology Used

### Spec-Driven Development
- **Requirements First**: Clear definition of what the system must do
- **Property-Based Testing**: Validation of universal properties
- **Infrastructure as Code**: Reproducible deployment
- **Incremental Implementation**: Development through discrete tasks

### Design Principles
- **Genericity**: Reusable system for any RSS feed
- **Security**: Minimal privileges and sensitive information protection
- **Resilience**: Robust error handling and fallback mechanisms
- **Monitoring**: Complete logging and observability metrics

## Technology Choices

### Core Stack
- **Python 3.12**: Main language
- **AWS Lambda**: Serverless compute
- **DynamoDB**: Deduplication storage
- **Amazon Bedrock**: AI service for summaries
- **EventBridge**: Execution scheduling

### Testing Framework
- **pytest**: Main testing framework
- **hypothesis**: Property-based testing
- **ruff**: Linting and formatting

### Infrastructure
- **CloudFormation**: Infrastructure as Code
- **AWS Secrets Manager**: Secure credential management
- **CloudWatch**: Logging and monitoring

## Architectural Decisions

### 1. Serverless vs Container
**Choice**: AWS Lambda serverless
**Rationale**:
- Optimal costs for daily execution
- Automatic scaling
- Reduced maintenance

### 2. AI Service
**Choice**: Amazon Bedrock with extractive fallback
**Rationale**:
- Superior summary quality
- Native AWS integration
- Fallback for resilience

### 3. Deduplication Storage
**Choice**: DynamoDB with TTL
**Rationale**:
- High performance for lookups
- Automatic TTL cleanup
- Serverless integration

### 4. Testing Strategy
**Choice**: Dual testing (unit + property-based)
**Rationale**:
- Property tests for universal correctness
- Unit tests for specific cases
- Complete coverage with complementary approach

## Correctness Properties

The system implements 18 testable correctness properties that guarantee:
- Configurability of customizable feeds
- Security of tokens and sensitive information
- Resilience to errors and fallback
- Consistent summary format
- Reliable deduplication

## Results

### Implemented Features
- ✅ Generic RSS-to-Telegram system
- ✅ Single-command deployment
- ✅ AI Italian summaries with fallback
- ✅ DynamoDB deduplication with TTL
- ✅ Complete CloudWatch monitoring
- ✅ Complete test suite (unit + property-based)
- ✅ Infrastructure as Code
- ✅ Complete documentation

### Project Metrics
- **Lines of code**: ~2000 LOC
- **Test coverage**: >90%
- **Tested properties**: 18
- **Components**: 6 main modules
- **Development time**: Iterative spec-driven process

## Reproducibility

This document serves as a reference to:
1. Understand decisions made during development
2. Replicate the approach for similar projects
3. Keep track of the AI-assisted development process
4. Provide context for future modifications or extensions

## Notes for Future Developers

- The system is designed to be generic and reusable
- Configuration is completely externalized
- Property-based tests validate universal behaviors
- The architecture supports future extensions (new feed formats, AI services, etc.)
- Documentation is kept synchronized with code
