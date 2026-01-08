# AI Models Guide for Summaries

This document explains how to configure and use different Amazon Bedrock models to generate Italian summaries.

> **Available languages**: [English (current)](MODELS.md) | [Italiano](MODELS.it.md)

## Supported Models

The bot automatically supports two types of models:

### 1. Amazon Nova Micro (Default)
- **Model ID**: `amazon.nova-micro-v1:0` or `eu.amazon.nova-micro-v1:0`
- **Advantages**: 
  - Cost-effective for high volume
  - Fast (< 1 second per summary)
  - Good Italian quality
  - Available via cross-region inference profile
- **Cost**: ~$0.000035 per 1K input tokens, ~$0.00014 per 1K output tokens

### 2. Llama 3.2 3B Instruct
- **Model ID**: `us.meta.llama3-2-3b-instruct-v1:0`
- **Advantages**:
  - Excellent for summaries and translations
  - Good context understanding
  - Native multilingual support
- **Cost**: ~$0.00015 per 1K input tokens, ~$0.0002 per 1K output tokens
- **Note**: Requires model access in your AWS region

## How to Change Model

### Option 1: Modify Infrastructure Template

Edit `infrastructure/template.yaml`:

```yaml
Parameters:
  BedrockModelId:
    Type: String
    Default: 'us.meta.llama3-2-3b-instruct-v1:0'  # Change here
    Description: 'Amazon Bedrock model ID for AI summarization'
```

### Option 2: Modify Pipeline Template

If using CodePipeline, edit `infrastructure/pipeline-template.yaml`:

```yaml
Environment:
  Variables:
    BEDROCK_MODEL_ID: 'us.meta.llama3-2-3b-instruct-v1:0'  # Change here
```

### Option 3: Environment Variable

Set the environment variable directly in Lambda:

```bash
aws lambda update-function-configuration \
  --function-name another-rss-telegram-bot-processor \
  --environment Variables={BEDROCK_MODEL_ID=us.meta.llama3-2-3b-instruct-v1:0}
```

## Required IAM Permissions

The Lambda role already includes permissions for both Nova Micro and Llama 3.2 models.

The IAM policy in `infrastructure/template.yaml` includes:

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
          - !Sub 'arn:aws:bedrock:*::foundation-model/*'
```

## Verify Model Availability

Before using a model, verify it's available in your region:

```bash
aws bedrock list-foundation-models \
  --region eu-west-1 \
  --query "modelSummaries[?contains(modelId, 'llama3-2-3b')]"
```

## Model Comparison

| Feature | Nova Micro | Llama 3.2 3B |
|---------|------------|--------------|
| Speed | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Cost | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Italian Quality | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Follow Instructions | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Availability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## Adding Other Models

To support other Bedrock models (e.g., Claude, Mistral):

1. Identify the model's API format in [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html)

2. Modify `src/summarize.py` in the `bedrock_summarize()` method:

```python
# Example for Claude
if "claude" in self.config.model_id.lower():
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": self.config.max_tokens,
        "temperature": 0.3
    }
    # Parse response
    summary_text = response_body["content"][0]["text"]
```

3. Update IAM permissions to include the new model

4. Test thoroughly before production deployment

## Recommendations

- **For production**: Use Nova Micro for best cost/performance ratio
- **For maximum quality**: Use Llama 3.2 3B or larger models
- **For multilingual**: Llama 3.2 has better native support
- **For limited budget**: Nova Micro is the most economical choice

## Local Fallback

If Bedrock is unavailable or fails, the bot automatically uses a local extractive summarization system that:
- Doesn't require external APIs
- Is always available
- Always uses "Perché ti può interessare" (correct format)
- Has lower quality but is reliable
