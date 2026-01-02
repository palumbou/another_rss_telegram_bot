"""Unit tests for Telegram Publisher."""

from src.config import TelegramConfig
from src.models import Summary
from src.telegram import TelegramPublisher


class TestTelegramPublisherUnit:
    """Unit tests for TelegramPublisher."""

    def setup_method(self):
        """Set up test configuration."""
        self.config = TelegramConfig(bot_token="test_token", chat_id="test_chat_id")
        self.publisher = TelegramPublisher(self.config)

    def test_format_message_html_specific(self):
        """Test HTML formatting with specific example."""
        summary = Summary(
            title="AWS Lambda Introduces New Features",
            bullets=[
                "Support for Python 3.12 runtime",
                "Enhanced monitoring capabilities",
                "Improved cold start performance",
            ],
            why_it_matters="Developers can build more efficient serverless applications",
        )

        link = "https://aws.amazon.com/blogs/aws/example-post"

        formatted_message = self.publisher.format_message(summary, link)

        # Verify HTML structure
        assert formatted_message.startswith("<b>AWS Lambda Introduces New Features</b>")
        assert "• Support for Python 3.12 runtime" in formatted_message
        assert "• Enhanced monitoring capabilities" in formatted_message
        assert "• Improved cold start performance" in formatted_message
        assert (
            "<i>Perché conta:</i> Developers can build more efficient serverless applications"
            in formatted_message
        )
        assert (
            f'🔗 <a href="{link}">Leggi l\'articolo completo</a>' in formatted_message
        )

        # Verify proper line breaks
        lines = formatted_message.split("\n")
        assert (
            len(lines) >= 7
        )  # Title, empty, 3 bullets, empty, why it matters, empty, link

    def test_format_message_special_characters(self):
        """Test handling of special HTML characters."""
        summary = Summary(
            title="Test & Development <Guide>",
            bullets=[
                "Use 'quotes' and \"double quotes\"",
                "Handle <tags> & ampersands",
                "Process > and < symbols",
            ],
            why_it_matters="Proper escaping prevents HTML injection & formatting issues",
        )

        link = "https://example.com/test?param=value&other=test"

        formatted_message = self.publisher.format_message(summary, link)

        # Verify HTML escaping
        assert "&amp;" in formatted_message  # & should be escaped
        assert "&lt;" in formatted_message  # < should be escaped
        assert "&gt;" in formatted_message  # > should be escaped
        assert "&#x27;" in formatted_message  # ' should be escaped
        assert "&quot;" in formatted_message  # " should be escaped

        # Verify the link is not escaped (it should remain as valid HTML)
        assert f'<a href="{link}">Leggi l\'articolo completo</a>' in formatted_message

    def test_html_escaping_edge_cases(self):
        """Test HTML escaping with edge cases."""
        # Test empty strings
        assert self.publisher._escape_html("") == ""
        assert self.publisher._escape_html(None) == ""

        # Test strings with only special characters
        assert self.publisher._escape_html("&<>\"'") == "&amp;&lt;&gt;&quot;&#x27;"

        # Test mixed content
        text = 'Normal text & <special> content with "quotes"'
        escaped = self.publisher._escape_html(text)
        expected = "Normal text &amp; &lt;special&gt; content with &quot;quotes&quot;"
        assert escaped == expected

    def test_format_message_italian_content(self):
        """Test formatting with Italian content."""
        summary = Summary(
            title="Nuove Funzionalità di AWS Lambda",
            bullets=[
                "Supporto per runtime Python 3.12",
                "Capacità di monitoraggio migliorate",
                "Prestazioni di avvio a freddo ottimizzate",
            ],
            why_it_matters="Gli sviluppatori possono creare applicazioni serverless più efficienti",
        )

        link = "https://aws.amazon.com/it/blogs/aws/esempio"

        formatted_message = self.publisher.format_message(summary, link)

        # Verify Italian content is preserved
        assert "Nuove Funzionalità di AWS Lambda" in formatted_message
        assert "Gli sviluppatori possono creare" in formatted_message
        assert "Leggi l'articolo completo" in formatted_message

        # Verify proper HTML structure is maintained
        assert formatted_message.startswith("<b>")
        assert "<i>Perché conta:</i>" in formatted_message
        assert "🔗 <a href=" in formatted_message

    def test_format_message_minimal_content(self):
        """Test formatting with minimal content."""
        summary = Summary(title="Short", bullets=["One"], why_it_matters="Brief")

        link = "https://example.com"

        formatted_message = self.publisher.format_message(summary, link)

        # Verify all required elements are present even with minimal content
        assert "<b>Short</b>" in formatted_message
        assert "• One" in formatted_message
        assert "<i>Perché conta:</i> Brief" in formatted_message
        assert f'<a href="{link}">Leggi l\'articolo completo</a>' in formatted_message

    def test_format_message_maximum_bullets(self):
        """Test formatting with maximum number of bullets."""
        summary = Summary(
            title="Test with Three Bullets",
            bullets=["First bullet point", "Second bullet point", "Third bullet point"],
            why_it_matters="Testing maximum bullet capacity",
        )

        link = "https://example.com/test"

        formatted_message = self.publisher.format_message(summary, link)

        # Count bullet points in formatted message
        bullet_count = formatted_message.count("• ")
        assert bullet_count == 3, f"Expected 3 bullets, found {bullet_count}"

        # Verify all bullets are present
        assert "• First bullet point" in formatted_message
        assert "• Second bullet point" in formatted_message
        assert "• Third bullet point" in formatted_message
