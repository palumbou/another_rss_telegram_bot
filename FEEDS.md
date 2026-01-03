# RSS Feeds Configuration

> **Available languages**: [English (current)](FEEDS.md) | [Italiano](FEEDS.it.md)

## Overview

The `feeds.json` file contains the list of RSS feeds that the bot will monitor. This file is included in the deployment package and read by the Lambda function at runtime.

## File Format

```json
{
  "feeds": [
    {
      "url": "https://example.com/feed.xml",
      "name": "Example Feed",
      "enabled": true
    }
  ]
}
```

### Fields

- **url** (required): The RSS/Atom feed URL
- **name** (optional): Human-readable name for the feed
- **enabled** (optional): Whether this feed is active (default: true)

## Default Feeds

The default `feeds.json` includes AWS-related feeds:

- AWS Blog
- AWS What's New
- AWS Security Blog
- AWS Compute Blog
- AWS Database Blog

## Customization

### Option 1: Edit feeds.json

Edit the `feeds.json` file in the project root:

```json
{
  "feeds": [
    {
      "url": "https://techcrunch.com/feed/",
      "name": "TechCrunch",
      "enabled": true
    },
    {
      "url": "https://www.theverge.com/rss/index.xml",
      "name": "The Verge",
      "enabled": true
    }
  ]
}
```

Then deploy with:

```bash
./scripts/deploy.sh --update-code
```

### Option 2: Use Custom Feeds File

Create your own feeds file and specify it during deployment:

```bash
./scripts/deploy.sh \
  --telegram-token "YOUR_TOKEN" \
  --chat-id "YOUR_CHAT_ID" \
  --feeds-file /path/to/my-feeds.json
```

## Disabling Feeds

To temporarily disable a feed without removing it:

```json
{
  "feeds": [
    {
      "url": "https://example.com/feed.xml",
      "name": "Example Feed",
      "enabled": false
    }
  ]
}
```

## Validation

The deployment script automatically validates the feeds file:

- Checks JSON syntax
- Verifies required structure
- Counts enabled feeds
- Reports validation errors

## Best Practices

1. **Test feeds first**: Verify feed URLs are accessible before deployment
2. **Use descriptive names**: Help identify feeds in logs
3. **Start small**: Begin with a few feeds and add more gradually
4. **Monitor performance**: More feeds = longer execution time
5. **Check feed formats**: Ensure feeds are RSS 2.0 or Atom compatible

## Troubleshooting

### Feed Not Found Error

If you see "Feeds file not found" in logs:
- Ensure `feeds.json` is in the project root
- Verify the file is included in the deployment package
- Check file permissions

### No Enabled Feeds

If you see "No enabled feeds found":
- Check that at least one feed has `"enabled": true`
- Verify the JSON structure is correct
- Ensure feeds array is not empty

### Invalid JSON

If deployment fails with JSON validation error:
- Use a JSON validator (e.g., jsonlint.com)
- Check for missing commas or brackets
- Verify quotes are properly escaped

## Examples

### Tech News Feeds

```json
{
  "feeds": [
    {
      "url": "https://techcrunch.com/feed/",
      "name": "TechCrunch",
      "enabled": true
    },
    {
      "url": "https://www.theverge.com/rss/index.xml",
      "name": "The Verge",
      "enabled": true
    },
    {
      "url": "https://arstechnica.com/feed/",
      "name": "Ars Technica",
      "enabled": true
    }
  ]
}
```

### Development Blogs

```json
{
  "feeds": [
    {
      "url": "https://github.blog/feed/",
      "name": "GitHub Blog",
      "enabled": true
    },
    {
      "url": "https://stackoverflow.blog/feed/",
      "name": "Stack Overflow Blog",
      "enabled": true
    },
    {
      "url": "https://dev.to/feed",
      "name": "DEV Community",
      "enabled": true
    }
  ]
}
```

---

*For more information, see the main [README.md](README.md)*
