# tests/core/test_logging_config.py
import logging
import pytest
from unittest.mock import MagicMock, patch
from core.logging_config import SensitiveDataFilter, setup_logging


# ==============================================================================
# HELPERS
# ==============================================================================

def make_log_record(msg: str, args=()) -> logging.LogRecord:
    """Helper — builds a LogRecord with a given message."""
    record = logging.LogRecord(
        name="api_integration",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg=msg,
        args=args,
        exc_info=None
    )
    return record


# ==============================================================================
# SensitiveDataFilter Tests
# ==============================================================================

class TestSensitiveDataFilter:

    def test_filter_returns_true_for_safe_message(self):
        """Filter always returns True (allows the record through)."""
        f = SensitiveDataFilter()
        record = make_log_record("This is a safe log message")
        assert f.filter(record) is True

    def test_filter_returns_true_after_masking(self):
        """Filter returns True even when masking occurs."""
        with patch("core.logging_config.settings") as mock_settings:
            mock_settings.EBAY_CLIENT_SECRET = "supersecret"
            f = SensitiveDataFilter()
            record = make_log_record("Token: supersecret was used")
            result = f.filter(record)
            assert result is True

    def test_filter_masks_ebay_client_secret(self):
        """eBay client secret in log message is replaced with ******."""
        with patch("core.logging_config.settings") as mock_settings:
            mock_settings.EBAY_CLIENT_SECRET = "supersecret"
            f = SensitiveDataFilter()
            record = make_log_record("Token: supersecret was used")
            f.filter(record)
            assert "supersecret" not in str(record.msg)
            assert "******" in str(record.msg)

    def test_filter_preserves_safe_message_content(self):
        """Safe log messages are not modified."""
        with patch("core.logging_config.settings") as mock_settings:
            mock_settings.EBAY_CLIENT_SECRET = "supersecret"
            f = SensitiveDataFilter()
            record = make_log_record("HTTP Error: 401 | URL: https://api.ebay.com")
            f.filter(record)
            assert "HTTP Error: 401" in str(record.msg)

    def test_filter_masks_all_occurrences_of_secret(self):
        """All occurrences of the secret are masked, not just the first."""
        with patch("core.logging_config.settings") as mock_settings:
            mock_settings.EBAY_CLIENT_SECRET = "supersecret"
            f = SensitiveDataFilter()
            record = make_log_record(
                "Secret: supersecret and again: supersecret"
            )
            f.filter(record)
            assert "supersecret" not in str(record.msg)
            assert str(record.msg).count("******") == 2

    def test_filter_handles_none_secret(self):
        """Filter handles None secret gracefully without crashing."""
        with patch("core.logging_config.settings") as mock_settings:
            mock_settings.EBAY_CLIENT_SECRET = None
            f = SensitiveDataFilter()
            record = make_log_record("Some log message")
            result = f.filter(record)
            assert result is True
            assert record.msg == "Some log message"

    def test_filter_handles_empty_secret(self):
        """Filter handles empty string secret gracefully."""
        with patch("core.logging_config.settings") as mock_settings:
            mock_settings.EBAY_CLIENT_SECRET = ""
            f = SensitiveDataFilter()
            record = make_log_record("Some log message")
            result = f.filter(record)
            assert result is True

    def test_filter_handles_non_string_message(self):
        """Filter converts non-string messages to string before masking."""
        with patch("core.logging_config.settings") as mock_settings:
            mock_settings.EBAY_CLIENT_SECRET = "supersecret"
            f = SensitiveDataFilter()
            record = make_log_record({"key": "supersecret"})
            result = f.filter(record)
            assert result is True

    def test_filter_handles_empty_message(self):
        """Filter handles empty log message without crashing."""
        with patch("core.logging_config.settings") as mock_settings:
            mock_settings.EBAY_CLIENT_SECRET = "supersecret"
            f = SensitiveDataFilter()
            record = make_log_record("")
            result = f.filter(record)
            assert result is True

    def test_filter_partial_secret_not_masked(self):
        """Partial secret match is not masked — only exact match."""
        with patch("core.logging_config.settings") as mock_settings:
            mock_settings.EBAY_CLIENT_SECRET = "supersecret"
            f = SensitiveDataFilter()
            record = make_log_record("Token: superse")  # partial
            f.filter(record)
            assert "superse" in str(record.msg)
            assert "******" not in str(record.msg)


# ==============================================================================
# setup_logging Tests
# ==============================================================================

class TestSetupLogging:

    def test_returns_logger_instance(self):
        """setup_logging returns a Logger instance."""
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)

    def test_logger_name_is_api_integration(self):
        """Logger is named 'api_integration'."""
        logger = setup_logging()
        assert logger.name == "api_integration"

    def test_logger_level_is_info(self):
        """Logger level is set to INFO."""
        logger = setup_logging()
        assert logger.level == logging.INFO

    def test_logger_has_at_least_one_handler(self):
        """Logger has at least one handler attached."""
        logger = setup_logging()
        assert len(logger.handlers) >= 1

    def test_handler_is_stream_handler(self):
        """At least one handler is a StreamHandler."""
        logger = setup_logging()
        handler_types = [type(h) for h in logger.handlers]
        assert logging.StreamHandler in handler_types

    def test_handler_has_sensitive_data_filter(self):
        """StreamHandler has SensitiveDataFilter attached."""
        logger = setup_logging()
        stream_handler = next(
            h for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
        )
        filter_types = [type(f) for f in stream_handler.filters]
        assert SensitiveDataFilter in filter_types

    def test_handler_has_formatter(self):
        """StreamHandler has a formatter set."""
        logger = setup_logging()
        stream_handler = next(
            h for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
        )
        assert stream_handler.formatter is not None

    def test_formatter_includes_timestamp(self):
        """Formatter includes %(asctime)s for timestamps."""
        logger = setup_logging()
        stream_handler = next(
            h for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
        )
        assert "asctime" in stream_handler.formatter._fmt

    def test_formatter_includes_log_level(self):
        """Formatter includes %(levelname)s."""
        logger = setup_logging()
        stream_handler = next(
            h for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
        )
        assert "levelname" in stream_handler.formatter._fmt

    def test_formatter_includes_message(self):
        """Formatter includes %(message)s."""
        logger = setup_logging()
        stream_handler = next(
            h for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
        )
        assert "message" in stream_handler.formatter._fmt


# ==============================================================================
# Secret Masking Integration Tests
# ==============================================================================

class TestSensitiveDataFilterIntegration:

    def test_secret_does_not_appear_in_actual_log_output(self, capfd):
        """End-to-end: secret never appears in actual console output."""
        with patch("core.logging_config.settings") as mock_settings:
            mock_settings.EBAY_CLIENT_SECRET = "my_real_secret"
            logger = setup_logging()
            logger.error("Auth failed with secret: my_real_secret")
            captured = capfd.readouterr()
            assert "my_real_secret" not in captured.err
            assert "******" in captured.err

    def test_safe_message_appears_in_log_output(self, capfd):
        """End-to-end: safe messages appear unmodified in output."""
        with patch("core.logging_config.settings") as mock_settings:
            mock_settings.EBAY_CLIENT_SECRET = "my_real_secret"
            logger = setup_logging()
            logger.error("HTTP Error: 401 Unauthorized")
            captured = capfd.readouterr()
            assert "HTTP Error: 401 Unauthorized" in captured.err


# ==============================================================================
# Gap Documentation Tests (TDD revealing design issues)
# ==============================================================================

class TestSensitiveDataFilterGaps:

    def test_only_masks_ebay_secret_not_other_secrets(self):
        """
        Documents gap: filter only masks EBAY_CLIENT_SECRET.
        Other secrets like TOKEN_SECRET_KEY are not masked.
        Consider extending filter to cover all sensitive settings.
        """
        with patch("core.logging_config.settings") as mock_settings:
            mock_settings.EBAY_CLIENT_SECRET = "ebay_secret"
            mock_settings.TOKEN_SECRET_KEY = "jwt_secret"
            f = SensitiveDataFilter()
            record = make_log_record("jwt_secret leaked")
            f.filter(record)
            # jwt_secret is NOT masked — documents the gap
            assert "jwt_secret" in str(record.msg)

    def test_secret_in_args_not_masked(self):
        """
        Documents gap: secrets in record.args are not masked.
        Python logging formats msg % args — args bypass the filter.
        Consider masking record.args as well.
        """
        with patch("core.logging_config.settings") as mock_settings:
            mock_settings.EBAY_CLIENT_SECRET = "supersecret"
            f = SensitiveDataFilter()
            record = make_log_record(
                "Auth with token: %s",
                args=("supersecret",)
            )
            f.filter(record)
            # args are not masked — documents the gap
            assert "supersecret" in str(record.args)