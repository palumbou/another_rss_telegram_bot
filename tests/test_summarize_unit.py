"""Unit tests for Summarizer with specific scenarios."""

import json
from datetime import datetime
from unittest.mock import Mock, patch

from src.config import BedrockConfig
from src.models import FeedItem, Summary
from src.summarize import Summarizer


class TestSummarizerUnit:
    """Unit tests for Summarizer with specific content and error scenarios."""

    def test_italian_content_summarization(self):
        """
        Test summarization with specific Italian content.
        **Validates: Requirements 6.1**
        """
        # Italian content for testing
        italian_content = """
        Amazon Web Services ha annunciato oggi il lancio di una nuova funzionalità per AWS Lambda
        che permette agli sviluppatori di utilizzare container personalizzati. Questa innovazione
        rappresenta un passo importante verso la modernizzazione delle applicazioni serverless.

        La nuova funzionalità consente di deployare funzioni Lambda utilizzando immagini Docker
        personalizzate fino a 10 GB di dimensione. Gli sviluppatori possono ora utilizzare
        qualsiasi linguaggio di programmazione e includere dipendenze specifiche nei loro container.

        Secondo gli ingegneri di AWS, questa funzionalità risolve molte limitazioni precedenti
        e apre nuove possibilità per l'adozione di architetture serverless in contesti enterprise.
        """

        config = BedrockConfig()

        with patch("boto3.client"):
            summarizer = Summarizer(config)
            summarizer.bedrock_client = (
                None  # Force fallback to test extractive summarization
            )

            feed_item = FeedItem(
                title="AWS Lambda supporta container personalizzati",
                link="https://aws.amazon.com/blogs/aws/new-lambda-containers",
                published=datetime.now(),
                content=italian_content,
                feed_url="https://aws.amazon.com/blogs/aws/feed/",
            )

            result = summarizer.summarize(feed_item)

            # Verify the summary structure
            assert isinstance(result, Summary)
            assert len(result.bullets) == 3
            assert result.title is not None
            assert result.why_it_matters is not None

            # Verify content is in Italian context (should contain relevant terms)
            summary_text = (
                f"{result.title} {' '.join(result.bullets)} {result.why_it_matters}"
            )
            # The summary should contain some meaningful content from the original
            assert len(summary_text.strip()) > 50  # Should have substantial content

    def test_bedrock_access_denied_error(self):
        """
        Test handling of Bedrock AccessDenied error.
        **Validates: Requirements 6.3**
        """
        from botocore.exceptions import ClientError

        config = BedrockConfig()

        with patch("boto3.client") as mock_boto_client:
            mock_client = Mock()
            mock_boto_client.return_value = mock_client

            # Mock AccessDenied error
            error_response = {
                "Error": {
                    "Code": "AccessDeniedException",
                    "Message": "User is not authorized to perform: bedrock:InvokeModel",
                }
            }
            mock_client.invoke_model.side_effect = ClientError(
                error_response, "InvokeModel"
            )

            summarizer = Summarizer(config)

            feed_item = FeedItem(
                title="Test Article",
                link="https://example.com/test",
                published=datetime.now(),
                content="This is a test article with enough content to generate a meaningful summary. It contains multiple sentences and should provide enough material for extractive summarization to work properly.",
                feed_url="https://example.com/feed",
            )

            # Should handle the error gracefully and use fallback
            result = summarizer.summarize(feed_item)

            assert isinstance(result, Summary)
            assert len(result.bullets) == 3
            assert result.title is not None
            assert result.why_it_matters is not None

            # Verify that Bedrock was attempted (mock was called)
            assert mock_client.invoke_model.called

    def test_bedrock_successful_response(self):
        """
        Test successful Bedrock response parsing.
        **Validates: Requirements 6.1**
        """
        config = BedrockConfig()

        with patch("boto3.client") as mock_boto_client:
            mock_client = Mock()
            mock_boto_client.return_value = mock_client

            # Mock successful Bedrock response
            mock_bedrock_response = {
                "content": [
                    {
                        "text": "Nuova funzionalità AWS Lambda\n• Supporto per container Docker personalizzati\n• Immagini fino a 10 GB di dimensione\n• Maggiore flessibilità per sviluppatori\nPerché conta: Rivoluziona lo sviluppo serverless enterprise"
                    }
                ]
            }

            mock_response = {"body": Mock()}
            mock_response["body"].read.return_value = json.dumps(mock_bedrock_response)
            mock_client.invoke_model.return_value = mock_response

            summarizer = Summarizer(config)

            feed_item = FeedItem(
                title="AWS Lambda Container Support",
                link="https://example.com/test",
                published=datetime.now(),
                content="AWS Lambda now supports custom containers...",
                feed_url="https://example.com/feed",
            )

            result = summarizer.summarize(feed_item)

            # Verify the summary was parsed correctly from Bedrock response
            assert isinstance(result, Summary)
            assert result.title == "Nuova funzionalità AWS Lambda"
            assert len(result.bullets) == 3
            assert "Supporto per container Docker personalizzati" in result.bullets[0]
            assert (
                result.why_it_matters == "Rivoluziona lo sviluppo serverless enterprise"
            )

    def test_bedrock_empty_response(self):
        """
        Test handling of empty Bedrock response.
        **Validates: Requirements 6.3**
        """
        config = BedrockConfig()

        with patch("boto3.client") as mock_boto_client:
            mock_client = Mock()
            mock_boto_client.return_value = mock_client

            # Mock empty Bedrock response
            mock_response = {"body": Mock()}
            mock_response["body"].read.return_value = '{"content": []}'
            mock_client.invoke_model.return_value = mock_response

            summarizer = Summarizer(config)

            feed_item = FeedItem(
                title="Test Article",
                link="https://example.com/test",
                published=datetime.now(),
                content="This is test content for summarization with multiple sentences. It should provide enough material for the fallback summarization to work correctly.",
                feed_url="https://example.com/feed",
            )

            # Should detect empty response and use fallback
            result = summarizer.summarize(feed_item)

            assert isinstance(result, Summary)
            assert len(result.bullets) == 3
            assert result.title is not None
            assert result.why_it_matters is not None

    def test_format_summary_edge_cases(self):
        """
        Test format_summary method with various edge cases.
        **Validates: Requirements 6.2**
        """
        config = BedrockConfig()

        with patch("boto3.client"):
            summarizer = Summarizer(config)

            # Test case 1: Empty input
            result = summarizer.format_summary("")
            assert isinstance(result, Summary)
            assert result.title == "Riassunto non disponibile"
            assert len(result.bullets) == 3

            # Test case 2: Malformed input (no bullets)
            result = summarizer.format_summary(
                "Just a title line\nSome random text\nMore text"
            )
            assert isinstance(result, Summary)
            assert result.title == "Just a title line"
            assert len(result.bullets) == 3  # Should be padded

            # Test case 3: Too many bullets (should be truncated to 3)
            input_text = """Title
• First bullet point
• Second bullet point
• Third bullet point
• Fourth bullet point
• Fifth bullet point
Perché conta: This is why it matters"""

            result = summarizer.format_summary(input_text)
            assert isinstance(result, Summary)
            assert len(result.bullets) == 3
            assert result.bullets[0] == "First bullet point"
            assert result.bullets[1] == "Second bullet point"
            assert result.bullets[2] == "Third bullet point"

    def test_fallback_with_html_content(self):
        """
        Test fallback summarization with HTML content.
        **Validates: Requirements 6.3**
        """
        config = BedrockConfig()

        with patch("boto3.client"):
            summarizer = Summarizer(config)
            summarizer.bedrock_client = None  # Force fallback

            html_content = """
            <p>Amazon Web Services ha <strong>annunciato</strong> una nuova funzionalità.</p>
            <div>Questa innovazione <em>rappresenta</em> un passo importante.</div>
            <script>alert('test');</script>
            <p>La funzionalità consente di utilizzare container personalizzati.</p>
            """

            feed_item = FeedItem(
                title="AWS News",
                link="https://example.com/test",
                published=datetime.now(),
                content=html_content,
                feed_url="https://example.com/feed",
            )

            result = summarizer.summarize(feed_item)

            # Verify HTML was cleaned and summary was generated
            assert isinstance(result, Summary)
            assert len(result.bullets) == 3

            # Verify no HTML tags in the result
            full_text = (
                f"{result.title} {' '.join(result.bullets)} {result.why_it_matters}"
            )
            assert "<" not in full_text
            assert ">" not in full_text
            assert "script" not in full_text.lower()
