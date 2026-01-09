# AI Models Guide for Summaries

This document explains how to configure and use different Amazon Bedrock models to generate Italian summaries.

> **Available languages**: [English (current)](MODELS.md) | [Italiano](MODELS.it.md)

## Supported Models

The bot supports three Amazon Bedrock models that you can choose at deployment time:

### 1. Amazon Nova Micro (Default)
- **Model ID**: `amazon.nova-micro-v1:0`
- **Selection**: `nova-micro`
- **Advantages**: 
  - Most cost-effective for high volume
  - Fast (< 1 second per summary)
  - Good Italian quality
  - Available via cross-region inference profile
- **Cost**: ~$0.000035 per 1K input tokens, ~$0.00014 per 1K output tokens
- **Monthly cost (150 articles)**: ~$0.015
- **Best for**: Production deployments with high volume and budget constraints

### 2. Mistral Large (Intelligent Regional Selection)
- **Model IDs**: 
  - `mistral.mistral-large-3-675b-instruct` (preferred, 6 regions)
  - `mistral.mistral-large-2402-v1:0` (fallback, 9 regions)
- **Selection**: `mistral-large`
- **Advantages**:
  - Excellent multilingual translation (EN→IT, FR, ES, DE)
  - Superior reasoning and context understanding
  - Mistral Large 3: 675B parameters (41B active - MoE), multimodal support
  - Mistral Large 24.02: Proven stability, text-only
  - Native multilingual support (not translation as fallback)
- **Cost**: ~$2.00 per 1M input tokens, ~$6.00 per 1M output tokens
- **Monthly cost (150 articles)**: ~$0.78
- **Regional availability**:
  - **Mistral Large 3** (newest): us-east-1, us-east-2, us-west-2, ap-northeast-1, ap-south-1, sa-east-1
  - **Mistral Large 24.02** (fallback): us-west-1, ap-southeast-2, ca-central-1, eu-west-1/2/3, and 20+ other regions
- **Best for**: Quality-focused deployments requiring excellent translation and reasoning

### 3. Llama 3.2 3B Instruct
- **Inference Profile ID**: Region-specific (automatically selected)
  - US regions: `us.meta.llama3-2-3b-instruct-v1:0`
  - EU regions: `eu.meta.llama3-2-3b-instruct-v1:0`
- **Selection**: `llama-3b`
- **Advantages**:
  - Excellent for summaries and translations
  - Superior context understanding
  - Native multilingual support
  - Better instruction following than Nova Micro
- **Cost**: ~$0.00015 per 1K input tokens, ~$0.0002 per 1K output tokens
- **Monthly cost (150 articles)**: ~$0.06
- **Best for**: Balanced quality and cost
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
          - !Sub 'arn:aws:bedrock:*:${AWS::AccountId}:inference-profile/*'
          - !Sub 'arn:aws:bedrock:*::foundation-model/*'
```

**Key points:**
- Nova Micro uses a foundation model ARN (region-specific)
- Llama 3.2 3B uses inference profile ARNs (wildcard for all profiles in your account)
- Permissions are granted for all inference profiles regardless of deployment region
- CloudFormation automatically selects the correct profile based on your region
- Wildcard patterns provide flexibility while maintaining security (scoped to your account)

## Multi-Region Support

The bot automatically supports deployment in **all AWS regions** where Bedrock is available:

### Automatic Region Detection

When you deploy with Llama 3.2 3B, CloudFormation automatically selects the correct inference profile for your region:

**Supported Regions:**
- **US**: us-east-1, us-east-2, us-west-1, us-west-2
- **EU**: eu-west-1, eu-west-2, eu-west-3, eu-central-1, eu-central-2, eu-north-1, eu-south-1, eu-south-2
- **APAC**: ap-northeast-1, ap-northeast-2, ap-northeast-3, ap-south-1, ap-south-2, ap-southeast-1, ap-southeast-2, ap-southeast-3, ap-southeast-4, ap-southeast-5, ap-southeast-7, ap-east-2
- **Canada**: ca-central-1, ca-west-1
- **South America**: sa-east-1
- **Middle East**: me-central-1, me-south-1, il-central-1
- **Africa**: af-south-1
- **Mexico**: mx-central-1

### How It Works

1. **Deploy to any region**: `./scripts/deploy.sh --region YOUR_REGION -m llama-3b`
2. **CloudFormation mapping**: Automatically selects US or EU inference profile
3. **Cross-region routing**: Bedrock routes requests to available model endpoints
4. **No manual configuration**: Everything is handled automatically

### Regional Inference Profiles

Llama 3.2 3B uses two regional inference profiles:
- **US profile** (`us.meta.llama3-2-3b-instruct-v1:0`): Used in US, Canada, APAC, South America, Middle East, Mexico
- **EU profile** (`eu.meta.llama3-2-3b-instruct-v1:0`): Used in EU, Israel, Africa

The CloudFormation template includes a complete mapping for all AWS commercial regions.

## Verify Model Availability

Before deploying with a specific model, verify it's available in your AWS region:

**Check Nova Micro availability:**
```bash
aws bedrock list-foundation-models \
  --region eu-west-1 \
  --query "modelSummaries[?contains(modelId, 'nova-micro')]"
```

**Check Llama 3.2 3B inference profile (region-specific):**
```bash
# For EU regions
aws bedrock get-inference-profile \
  --region eu-west-1 \
  --inference-profile-identifier eu.meta.llama3-2-3b-instruct-v1:0

# For US regions
aws bedrock get-inference-profile \
  --region us-east-1 \
  --inference-profile-identifier us.meta.llama3-2-3b-instruct-v1:0
```

**Note**: Llama 3.2 3B uses region-specific inference profiles that are automatically selected based on your deployment region:
- **US regions** (us-east-1, us-west-2, etc.): Uses `us.meta.llama3-2-3b-instruct-v1:0`
- **EU regions** (eu-west-1, eu-central-1, etc.): Uses `eu.meta.llama3-2-3b-instruct-v1:0`
- **Other regions** (APAC, CA, SA, ME, etc.): Automatically routes to the nearest inference profile

Nova Micro is available globally as a foundation model without regional profiles.

## Model Comparison

| Feature | Nova Micro | Mistral Large | Llama 3.2 3B |
|---------|------------|---------------|--------------|
| **Speed** | ⭐⭐⭐⭐⭐ Very Fast | ⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐ Fast |
| **Cost** | ⭐⭐⭐⭐⭐ Most Economical | ⭐⭐⭐ Moderate | ⭐⭐⭐⭐ Economical |
| **Italian Quality** | ⭐⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐⭐ Excellent |
| **Multilingual** | ⭐⭐⭐ Adequate | ⭐⭐⭐⭐⭐ Native | ⭐⭐⭐⭐ Good |
| **Instruction Following** | ⭐⭐⭐ Adequate | ⭐⭐⭐⭐⭐ Superior | ⭐⭐⭐⭐⭐ Superior |
| **Regional Availability** | ⭐⭐⭐⭐⭐ Worldwide | ⭐⭐⭐⭐ 15+ Regions | ⭐⭐⭐⭐⭐ All Regions |
| **Monthly Cost (150 articles)** | $0.015 | $0.78 | $0.06 |
| **Best Use Case** | High-volume production | Quality translations | Balanced quality/cost |
| **Deployment** | `./scripts/deploy.sh -m nova-micro` | `./scripts/deploy.sh -m mistral-large` | `./scripts/deploy.sh -m llama-3b` |

### Cost Breakdown (5 articles/day, 150/month)

**Assumptions per article:**
- Input: ~2000 tokens (article + prompt)
- Output: ~200 tokens (summary)

| Model | Cost/Article | Monthly Cost | Annual Cost |
|-------|--------------|--------------|-------------|
| **Nova Micro** | $0.0001 | **$0.015** | **$0.18** |
| **Llama 3.2 3B** | $0.0004 | **$0.06** | **$0.72** |
| **Mistral Large** | $0.0052 | **$0.78** | **$9.36** |

**Note**: Mistral Large costs ~50x more than Nova Micro but provides significantly better translation quality and reasoning capabilities.

### Choosing the Right Model

**Choose Nova Micro if:**
- You need the lowest cost per summary
- You're processing high volumes (1000+ articles/day)
- Speed is critical
- You need cross-region inference profiles
- Budget is the primary concern

**Choose Mistral Large if:**
- Translation quality is your top priority
- You need superior multilingual understanding (EN→IT, FR, ES, DE)
- You want the best reasoning and context comprehension
- You're willing to pay ~50x more for significantly better quality
- You need multimodal support (Large 3 only, in 6 regions)

**Choose Llama 3.2 3B if:**
- You want a balance between quality and cost
- Summary quality is important but budget matters
- You need better instruction following than Nova Micro
- Cost is ~4x Nova Micro but quality is much better

## Mistral Large: Intelligent Regional Selection

When you select `mistral-large`, the bot automatically chooses the best available Mistral model for your deployment region:

### Mistral Large 3 (Preferred - 6 Regions)
**Model ID**: `mistral.mistral-large-3-675b-instruct`

**Available in:**
- 🇺🇸 US: us-east-1, us-east-2, us-west-2
- 🌏 APAC: ap-northeast-1 (Tokyo), ap-south-1 (Mumbai)
- 🇧🇷 South America: sa-east-1 (São Paulo)

**Features:**
- ✅ 675B parameters (41B active - Mixture of Experts)
- ✅ Multimodal support (text + images)
- ✅ Latest model (December 2025)
- ✅ Best reasoning capabilities
- ✅ Extended thinking with step-by-step reasoning

### Mistral Large 24.02 (Fallback - 9+ Regions)
**Model ID**: `mistral.mistral-large-2402-v1:0`

**Available in:**
- 🇺🇸 US: us-west-1
- 🇨🇦 Canada: ca-central-1
- 🇪🇺 Europe: eu-west-1 (Ireland), eu-west-2 (London), eu-west-3 (Paris)
- 🌏 APAC: ap-southeast-2 (Sydney), and 20+ other regions

**Features:**
- ✅ Text-only (no multimodal)
- ✅ Proven stability and reliability
- ✅ Same excellent multilingual capabilities
- ✅ Wider regional availability

**How it works:**
1. You deploy with `--model mistral-large`
2. CloudFormation checks your deployment region
3. If region has Mistral Large 3 → uses Large 3 (newest, multimodal)
4. If region doesn't have Large 3 → uses Large 24.02 (stable, text-only)
5. Both versions provide excellent translation quality

**Example:**
```bash
# Deploy in us-east-1 → Gets Mistral Large 3 (675B MoE, multimodal)
./scripts/deploy.sh --region us-east-1 --model mistral-large

# Deploy in eu-west-1 → Gets Mistral Large 24.02 (text-only, stable)
./scripts/deploy.sh --region eu-west-1 --model mistral-large
```

Both versions will show in Telegram messages which specific model was used.

## Advanced Configuration

### Switching Models After Deployment

To change models after initial deployment, use the `--update-stack` flag with the desired model:

```bash
# Switch from Nova Micro to Mistral Large
./scripts/deploy.sh --update-stack --model mistral-large

# Switch from Mistral Large to Llama 3.2 3B
./scripts/deploy.sh --update-stack --model llama-3b

# Switch back to Nova Micro
./scripts/deploy.sh --update-stack --model nova-micro
```

The `--update-stack` flag updates only the CloudFormation stack parameters without redeploying code. This is faster and safer than a full redeployment. The Lambda function will use the new model on its next execution.

**Alternative: Full redeployment** (not recommended for model changes only):

```bash
# This works but redeploys everything (slower)
./scripts/deploy.sh -m mistral-large
```

The CloudFormation stack update will change the `BEDROCK_MODEL_ID` environment variable without affecting other resources.

### Manual Model Configuration

If you need to manually configure the model (not recommended), you can update the Lambda environment variable:

```bash
aws lambda update-function-configuration \
  --function-name another-rss-telegram-bot-processor \
  --environment Variables={BEDROCK_MODEL_ID=us.meta.llama3-2-3b-instruct-v1:0}
```

**Note**: The inference profile ID depends on your region. Use `us.meta.llama3-2-3b-instruct-v1:0` for US regions or `eu.meta.llama3-2-3b-instruct-v1:0` for EU regions.

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

### How Fallback Works

The fallback system uses **extractive summarization** - it extracts existing sentences from the article without understanding or translating the content:

**Process:**
1. **Text Cleaning**: Removes HTML tags and normalizes whitespace
2. **Sentence Splitting**: Splits text on `.!?` punctuation
3. **Simple Ranking**: Scores sentences based on:
   - Position (earlier sentences = higher score, 60% weight)
   - Length (longer sentences = higher score, 40% weight)
4. **Selection**: Takes the top 3 scored sentences as bullet points
5. **Title Generation**: Uses first 8 words of the top sentence
6. **"Why It Matters"**: Generated by keyword matching (searches for "ai", "security", "aws", etc.)

**Important Limitations:**
- ❌ **No Translation**: If the article is in English, the summary stays in English
- ❌ **No Understanding**: Doesn't comprehend context or meaning
- ❌ **No New Text**: Only extracts existing sentences, doesn't generate new content
- ✅ **Always Available**: Works without external dependencies
- ✅ **Fast**: No API calls, instant processing

**Example:**

*Original English Article:*
```
AWS announces new machine learning service. 
The service is fully managed for deep learning models.
Integration with S3 and other AWS services.
Pay-per-use pricing with no fixed costs.
```

*Fallback Output (stays in English):*
```
AWS announces new machine learning service

• AWS announces new machine learning service...
• The service is fully managed for deep learning models...
• Integration with S3 and other AWS services...

Perché conta: Novità cloud che potrebbero ottimizzare la tua infrastruttura

Fonte: https://...
```

Notice that only "Perché conta:" is in Italian (hardcoded), while the content remains in the original language.

**Recommendation:** Ensure Bedrock is properly configured to avoid relying on fallback for production use. The fallback is designed as an emergency backup, not a primary summarization method.

The fallback ensures your bot continues functioning even when Bedrock is unavailable.
