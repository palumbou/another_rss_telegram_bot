"""Property-based tests for Telegram Publisher."""

import time
from unittest.mock import patch

from hypothesis import given
from hypothesis import strategies as st

from src.config import TelegramConfig
from src.models import Summary
from src.telegram import TelegramPublisher


# Test data generators
@st.composite
def summary_strategy(draw):
    """Generate valid Summary objects."""
    title = draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
    bullets = draw(
        st.lists(
            st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
            min_size=1,
            max_size=3,
        )
    )
    why_it_matters = draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))

    return Summary(title=title, bullets=bullets, why_it_matters=why_it_matters)


@st.composite
def url_strategy(draw):
    """Generate valid URLs."""
    protocol = draw(st.sampled_from(["http", "https"]))
    domain = draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="-"
            ),
            min_size=3,
            max_size=20,
        ).filter(lambda x: x and not x.startswith("-") and not x.endswith("-"))
    )
    tld = draw(st.sampled_from(["com", "org", "net", "it", "co.uk"]))
    path = draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="/-_"
            ),
            max_size=50,
        )
    )

    url = f"{protocol}://{domain}.{tld}"
    if path and not path.startswith("/"):
        url += "/" + path
    elif path:
        url += path

    return url


class TestTelegramPublisherProperties:
    """Property-based tests for TelegramPublisher."""

    def setup_method(self):
        """Set up test configuration."""
        self.config = TelegramConfig(bot_token="test_token", chat_id="test_chat_id")
        self.publisher = TelegramPublisher(self.config)

    @given(summary=summary_strategy(), original_link=url_strategy())
    def test_property_13_inclusione_link_originale(self, summary, original_link):
        """
        **Feature: another-rss-telegram-bot, Property 13: Inclusione Link Originale**
        **Validates: Requirements 7.2**

        For any message sent to Telegram, it should contain the original article link.
        """
        # Format the message
        formatted_message = self.publisher.format_message(summary, original_link)

        # Verify the original link is included in the message
        assert (
            original_link in formatted_message
        ), f"Original link {original_link} not found in message: {formatted_message}"

        # Verify the link is properly formatted as HTML anchor
        expected_link_format = (
            f'<a href="{original_link}">Leggi l\'articolo completo</a>'
        )
        assert (
            expected_link_format in formatted_message
        ), f"Expected link format not found in message: {formatted_message}"

    @given(retry_count=st.integers(min_value=0, max_value=5))
    def test_property_14_retry_rate_limiting(self, retry_count):
        """
        **Feature: another-rss-telegram-bot, Property 14: Retry Rate Limiting**
        **Validates: Requirements 7.3**

        For any 429 error from Telegram API, the system should implement retry with exponential backoff.
        """
        # Test the handle_rate_limit method implements exponential backoff
        time.time()

        # Mock time.sleep to avoid actual delays in tests
        with patch("time.sleep") as mock_sleep:
            self.publisher.handle_rate_limit(retry_count)

            # Verify exponential backoff calculation
            expected_backoff = self.config.backoff_factor**retry_count
            mock_sleep.assert_called_once_with(expected_backoff)

        # Verify the backoff time increases exponentially
        expected_backoff = self.config.backoff_factor**retry_count
        assert expected_backoff >= 0, "Backoff time should be non-negative"

        # For retry_count > 0, backoff should be greater than base factor
        if retry_count > 0:
            base_backoff = self.config.backoff_factor**0  # Should be 1
            current_backoff = self.config.backoff_factor**retry_count
            assert (
                current_backoff >= base_backoff
            ), f"Backoff should increase: {current_backoff} >= {base_backoff}"

    @given(
        summary=summary_strategy(),
        original_link=url_strategy(),
        error_code=st.integers(min_value=400, max_value=599).filter(lambda x: x != 429),
    )
    def test_property_15_resilienza_errori_telegram(
        self, summary, original_link, error_code
    ):
        """
        **Feature: another-rss-telegram-bot, Property 15: Resilienza Errori Telegram**
        **Validates: Requirements 7.4**

        For any Telegram API error, the system should continue processing other messages.
        """
        import urllib.error

        # Mock urllib.request.urlopen to simulate various HTTP errors
        with patch("urllib.request.urlopen") as mock_urlopen:
            # Create an HTTPError with the given error code
            mock_error = urllib.error.HTTPError(
                url="https://api.telegram.org/bot/sendMessage",
                code=error_code,
                msg=f"HTTP {error_code} Error",
                hdrs={},
                fp=None,
            )
            mock_urlopen.side_effect = mock_error

            # The send_message method should handle the error gracefully
            result = self.publisher.send_message(summary, original_link)

            # Should return False for errors but not raise exceptions
            assert (
                result is False
            ), f"Expected False for HTTP {error_code} error, got {result}"

            # Verify the method was called (indicating it attempted to send)
            assert mock_urlopen.called, "Expected urlopen to be called"

        # Test with URLError (network issues)
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_error = urllib.error.URLError("Network unreachable")
            mock_urlopen.side_effect = mock_error

            # Should handle URLError gracefully
            result = self.publisher.send_message(summary, original_link)
            assert result is False, f"Expected False for URLError, got {result}"

        # Test with generic Exception
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("Unexpected error")

            # Should handle generic exceptions gracefully
            result = self.publisher.send_message(summary, original_link)
            assert (
                result is False
            ), f"Expected False for generic exception, got {result}"
