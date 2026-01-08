# AI Models Guide for Summaries

This document explains how to configure and use different Amazon Bedrock models to generate Italian summaries.

> **Available languages**: [English (current)](MODELS.md) | [Italiano](MODELS.it.md)

## Supported Models

The bot supports two Amazon Bedrock models that you can choose at deployment time:

### 1. Amazon Nova Micro (Default)
- **Model ID**: `amazon.nova-micro-v1:0`
- **Selection**: `nova-micro`
- **Advantages**: 
  - Cost-effective for high volume
  - Fast (< 1 second per summary)
  - Good Italian quality
  - Available via cross-region inference profile
- **Cost**: ~$0.000035 per 1K input tokens, ~$0.00014 per 1K output tokens
- **Best for**: Production deployments with high volume

### 2. Llama 3.2 3B Instruct
- **Model ID**: `us.meta.llama3-2-3b-instruct-v1:0`
- **Selection**: `llama-3b`
- **Advantages**:
  - Excellent for summaries and translations
  - Superior context understanding
  - Native multilingual support
  - Better instruction following
- **Cost**: ~$0.00015 per 1K input tokens, ~$0.0002 per 1K output tokens
- **Best for**: Quality-focused deployments
- **Note**: Requires model access in your AWS region

## How to Choose a Model at Deployment

You can select which model to use when deploying the stack using the deployment script's `-m` parameter.

### Deploy with Nova Micro (Default)

```bash
./scripts/deploy.sh -m nova-micro
```

Or simply omit the parameter (Nova Micro is the default):

```bash
./scripts/deploy.sh
```

### Deploy with Llama 3.2 3B

```bash
./scripts/deploy.sh -m llama-3b
```

### Full Deployment Examples

**Nova Micro deployment:**
```bash
./scripts/deploy.sh \
  -b another-rss-telegram-bot \
  -t YOUR_TELEGRAM_BOT_TOKEN \
  -c YOUR_TELEGRAM_CHAT_ID \
  -m nova-micro
```

**Llama 3.2 3B deployment:**
```bash
./scripts/deploy.sh \
  -b another-rss-telegram-bot \
  -t YOUR_TELEGRAM_BOT_TOKEN \
  -c YOUR_TELEGRAM_CHAT_ID \
  -m llama-3b
```

The deployment script automatically:
- Validates your model selection
- Configures CloudFormation with the correct model ID
- Sets up IAM permissions for the selected model
- Passes the model configuration to the Lambda function

## Understanding "Why It Matters" Phrases

The bot uses different Italian phrases to indicate the source of the summary:

### "Perché ti può interessare:" (Bedrock AI)
- **Used by**: All Bedrock models (Nova Micro, Llama 3.2 3B)
- **Meaning**: "Why you might be interested:"
- **Indicates**: AI-generated summary using Amazon Bedrock
- **Quality**: High-quality, contextual explanation

**Example:**
```
📰 Title: New AI Breakthrough in Healthcare
• First bullet point
• Second bullet point

💡 Perché ti può interessare: This advancement could revolutionize patient care...
```

### "Perché conta:" (Fallback)
- **Used by**: Local extractive summarization (when Bedrock is unavailable)
- **Meaning**: "Why it matters:"
- **Indicates**: Fallback summary without external AI
- **Quality**: Reliable but less contextual

**Example:**
```
📰 Title: New AI Breakthrough in Healthcare
• First bullet point
• Second bullet point

💡 Perché conta: This represents a significant development in the field...
```

This distinction helps users understand whether they're reading an AI-generated summary or a fallback summary.

## Required IAM Permissions

The CloudFormation templates automatically configure IAM permissions for both models. The Lambda execution role includes:

```yaml
- PolicyName: BedrockAccess
  PolicyDocument:
    Version: '2012-10-17'
    Statement:
      - Effect: Allow
        Action:
          - bedrock:InvokeModel
        Resource: 
          - !Sub 'arn:aws:bedrock:${AWS::Region}::foundation-model/amazon.nova-micro-v1:0'
          - !Sub 'arn:aws:bedrock:${AWS::Region}::foundation-model/us.meta.llama3-2-3b-instruct-v1:0'
```

**Key points:**
- Both model ARNs are explicitly included
- Permissions are granted regardless of which model you select
- This allows you to switch models by redeploying without IAM changes
- The wildcard pattern `arn:aws:bedrock:*::foundation-model/*` provides additional flexibility

## Verify Model Availability

Before deploying with a specific model, verify it's available in your AWS region:

**Check Nova Micro availability:**
```bash
aws bedrock list-foundation-models \
  --region eu-west-1 \
  --query "modelSummaries[?contains(modelId, 'nova-micro')]"
```

**Check Llama 3.2 3B availability:**
```bash
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'llama3-2-3b')]"
```

**Note**: Llama 3.2 3B is primarily available in US regions (us-east-1, us-west-2). Nova Micro is available globally through cross-region inference.

## Model Comparison

| Feature | Nova Micro | Llama 3.2 3B |
|---------|------------|--------------|
| **Speed** | ⭐⭐⭐⭐⭐ Very Fast | ⭐⭐⭐⭐ Fast |
| **Cost** | ⭐⭐⭐⭐⭐ Most Economical | ⭐⭐⭐⭐ Economical |
| **Italian Quality** | ⭐⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Excellent |
| **Instruction Following** | ⭐⭐⭐ Adequate | ⭐⭐⭐⭐⭐ Superior |
| **Regional Availability** | ⭐⭐⭐⭐⭐ Worldwide | ⭐⭐⭐⭐ US Regions |
| **Best Use Case** | High-volume production | Quality-focused deployments |
| **Deployment** | `./scripts/deploy.sh -m nova-micro` | `./scripts/deploy.sh -m llama-3b` |

### Choosing the Right Model

**Choose Nova Micro if:**
- You need the lowest cost per summary
- You're processing high volumes (1000+ articles/day)
- Speed is critical
- You need cross-region inference profiles

**Choose Llama 3.2 3B if:**
- Summary quality is your top priority
- You need better instruction following
- You want superior Italian language understanding
- Cost is less of a concern

## Advanced Configuration

### Switching Models After Deployment

To change models after initial deployment, simply redeploy with a different `-m` parameter:

```bash
# Switch from Nova Micro to Llama 3.2 3B
./scripts/deploy.sh -m llama-3b

# Switch back to Nova Micro
./scripts/deploy.sh -m nova-micro
```

The CloudFormation stack update will change the `BEDROCK_MODEL_ID` environment variable without affecting other resources.

### Manual Model Configuration

If you need to manually configure the model (not recommended), you can update the Lambda environment variable:

```bash
aws lambda update-function-configuration \
  --function-name another-rss-telegram-bot-processor \
  --environment Variables={BEDROCK_MODEL_ID=us.meta.llama3-2-3b-instruct-v1:0}
```

However, using the deployment script is preferred as it ensures consistency across all infrastructure components.

## Recommendations

**For production deployments:**
- Start with Nova Micro for best cost/performance ratio
- Monitor summary quality in your specific use case
- Switch to Llama 3.2 3B if quality improvements justify the cost

**For quality-focused deployments:**
- Use Llama 3.2 3B for superior Italian language understanding
- Expect ~4x higher costs compared to Nova Micro
- Better instruction following and contextual summaries

**For budget-constrained deployments:**
- Nova Micro is the most economical choice
- Still provides good quality Italian summaries
- Faster response times reduce Lambda execution costs

## Fallback Summarization

If Bedrock is unavailable or fails, the bot automatically uses a local extractive summarization system:

**Characteristics:**
- No external API dependencies
- Always available as a backup
- Uses "Perché conta:" phrase (different from Bedrock's "Perché ti può interessare:")
- Lower quality but reliable
- No additional costs

**When fallback is triggered:**
- Bedrock API errors or timeouts
- Model access denied (IAM or regional issues)
- Network connectivity problems
- Rate limiting or quota exceeded

The fallback ensures your bot continues functioning even when Bedrock is unavailable.
