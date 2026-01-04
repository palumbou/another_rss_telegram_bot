# Prompt Templates

> **Available languages**: [English (current)](README.md) | [Italiano](README.it.md)

This directory contains prompt templates used by the AI services in the RSS Telegram Bot system.

## bedrock_summary_template.txt

Main template used to generate summaries via Amazon Bedrock (Nova Micro).

### Required Summary Format

The template is designed to produce summaries with this exact structure:

```
[TITLE] (max 10 words)

• [BULLET 1] (max 30 words)
• [BULLET 2] (max 30 words)  
• [BULLET 3] (max 30 words)

Perché ti può interessare: [IMPACT] (max 20 words)

Fonte: [URL]
```

### Template Features

1. **Rigid Structure**: Fixed format ensures consistency in Telegram messages
2. **Word Limits**: Optimized for mobile device readability
3. **Italian Language**: All summaries are generated in Italian
4. **Accuracy**: Emphasis on faithfulness to original content
5. **Practicality**: Focus on practical benefits and user impact

### AI Model

The template is optimized for **Amazon Nova Micro** (`eu.amazon.nova-micro-v1:0`), which:
- Generates high-quality Italian summaries
- Responds quickly (< 1 second per summary)
- Is cost-effective for high-volume processing
- Available via cross-region inference profile in EU

### Customization

To modify the summary format:

1. Edit the template in `bedrock_summary_template.txt`
2. Update parsing logic in `src/summarize.py` (method `format_summary()`)
3. Test with different content types

**Important**: If you change the format, ensure the parsing logic in `src/summarize.py` matches the new structure.

### Template Variables

- `{content}`: Article content to summarize (automatically substituted)
- `{url}`: Article URL (automatically substituted)

### Best Practices

- Keep instructions clear and specific
- Include concrete examples in the prompt
- Specify precise length limits
- Emphasize accuracy and content faithfulness
- Use professional but accessible tone
- Be explicit about format requirements (e.g., "USE EXACTLY 'Perché ti può interessare:'")

### Fallback

If Bedrock is unavailable, the system uses extractive summarization that doesn't depend on this template but maintains a similar format for consistency. The fallback uses "Perché conta:" with context-aware suggestions based on content keywords.

### Testing

Test the template by:
- Deploying with test feeds (e.g., Hacker News, The Verge)
- Checking Telegram messages for correct format
- Verifying Italian quality and accuracy
- Monitoring CloudWatch logs for Bedrock success/failure
