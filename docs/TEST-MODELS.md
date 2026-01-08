# AI Models Testing Guide

This guide explains how to test different AI models to verify they work correctly.

> **Available languages**: [English (current)](TEST-MODELS.md) | [Italiano](TEST-MODELS.it.md)

## Quick Test with AWS CLI

### Test Nova Micro

```bash
aws bedrock-runtime invoke-model \
  --model-id amazon.nova-micro-v1:0 \
  --region eu-west-1 \
  --body '{
    "messages": [{"role": "user", "content": [{"text": "Summarize in Italian: AWS launched a new service"}]}],
    "inferenceConfig": {"max_new_tokens": 500, "temperature": 0.3}
  }' \
  --cli-binary-format raw-in-base64-out \
  output.json

cat output.json
```

### Test Llama 3.2 3B

```bash
aws bedrock-runtime invoke-model \
  --model-id us.meta.llama3-2-3b-instruct-v1:0 \
  --region us-east-1 \
  --body '{
    "prompt": "Summarize in Italian: AWS launched a new service",
    "max_gen_len": 500,
    "temperature": 0.3
  }' \
  --cli-binary-format raw-in-base64-out \
  output.json

cat output.json
```

## Test with Python Script

Use the provided test script:

```bash
# Test with Nova Micro (default)
python test_summarizer.py

# Test with Llama 3.2 3B
python test_summarizer.py us.meta.llama3-2-3b-instruct-v1:0
```

## Test Complete Bot

### 1. Local Test (without deployment)

The `test_summarizer.py` script tests the summarizer locally with a sample article.

### 2. Test Deployed Lambda

Invoke the Lambda with a test event:

```bash
aws lambda invoke \
  --function-name another-rss-telegram-bot-processor \
  --payload '{"test": true}' \
  --region eu-west-1 \
  response.json

cat response.json
```

### 3. Check Logs

Monitor CloudWatch logs to see which model was used:

```bash
aws logs tail /aws/lambda/another-rss-telegram-bot-processor \
  --follow \
  --region eu-west-1
```

Look for lines like:
- `Successfully generated summary using Bedrock Nova`
- `Successfully generated summary using Bedrock Llama`
- `Using enhanced fallback summarization`

## Verification Checklist

- [ ] Model is available in your AWS region
- [ ] You requested access to the model in Bedrock console
- [ ] IAM permissions include the model
- [ ] `BEDROCK_MODEL_ID` environment variable is set correctly
- [ ] Summary contains "Perché ti può interessare:" (not "Perché conta:")
- [ ] Summary format is correct (title + 3 bullets + why it matters)
- [ ] Messages are sent correctly to Telegram

## Troubleshooting

### Model doesn't respond

1. Verify availability:
```bash
aws bedrock list-foundation-models --region eu-west-1 | grep llama
```

2. Verify IAM permissions:
```bash
aws iam get-role-policy \
  --role-name another-rss-telegram-bot-lambda-role \
  --policy-name BedrockAccess
```

### AccessDeniedException

**Cause**: You don't have access to the model in your region.

**Solution**:
1. Go to AWS Bedrock console
2. Request access to the desired model
3. Wait for approval (usually immediate for standard models)

### ValidationException

**Cause**: Invalid request format for the model.

**Solution**:
1. Verify the model ID is correct
2. The code automatically detects model type (Nova vs Llama)
3. If using a different model, you may need to update `src/summarize.py`

## Metrics to Monitor

1. **Bedrock success rate**: How often it uses Bedrock vs fallback
2. **Latency**: Model response time
3. **Costs**: Tokens consumed per model
4. **Quality**: Manual verification of generated summaries
5. **Correct format**: "Perché ti può interessare" present

## Next Steps

After verifying everything works:

1. Monitor for a few days
2. Compare quality between Nova and Llama
3. Analyze actual costs
4. Choose the best model for your use case
5. Consider testing larger models if needed
