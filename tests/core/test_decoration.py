# tests/core/test_decoration.py
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from core.decoration import handle_api_errors


# ==============================================================================
# HELPERS
# ==============================================================================

def make_decorated(service_name="TestService", side_effect=None, return_value=None):
    """Helper to create a decorated async function."""
    mock_func = AsyncMock()
    if side_effect:
        mock_func.side_effect = side_effect
    else:
        mock_func.return_value = return_value
    mock_func.__name__ = "mock_func"
    mock_func.__wrapped__ = mock_func
    return handle_api_errors(service_name)(mock_func)


def make_http_status_error(status_code=500, body="Server Error", url="https://api.example.com"):
    """Helper to build a mock httpx.HTTPStatusError."""
    mock_request = MagicMock()
    mock_request.url = url
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = body
    return httpx.HTTPStatusError(
        message="HTTP Error",
        request=mock_request,
        response=mock_response
    )


# ==============================================================================
# Happy Path Tests
# ==============================================================================

class TestHandleApiErrorsHappyPath:

    @pytest.mark.asyncio
    async def test_returns_function_result_on_success(self):
        """Decorated function returns result normally when no error occurs."""
        decorated = make_decorated(return_value={"data": "ok"})
        result = await decorated()
        assert result == {"data": "ok"}

    @pytest.mark.asyncio
    async def test_returns_string_result(self):
        """Decorated function returns string result normally."""
        decorated = make_decorated(return_value="access.token.123")
        result = await decorated()
        assert result == "access.token.123"

    @pytest.mark.asyncio
    async def test_returns_none_result(self):
        """Decorated function returns None when function returns None."""
        decorated = make_decorated(return_value=None)
        result = await decorated()
        assert result is None

    @pytest.mark.asyncio
    async def test_passes_args_to_wrapped_function(self):
        """Arguments are passed through to the original function."""
        mock_func = AsyncMock(return_value="ok")
        mock_func.__name__ = "mock_func"
        decorated = handle_api_errors("TestService")(mock_func)
        await decorated("arg1", key="value")
        mock_func.assert_called_once_with("arg1", key="value")

    @pytest.mark.asyncio
    async def test_preserves_function_name(self):
        """functools.wraps preserves the original function name."""
        async def my_api_call():
            return "ok"
        decorated = handle_api_errors("TestService")(my_api_call)
        assert decorated.__name__ == "my_api_call"

    @pytest.mark.asyncio
    async def test_preserves_function_docstring(self):
        """functools.wraps preserves the original function docstring."""
        async def my_api_call():
            """Fetches data from API."""
            return "ok"
        decorated = handle_api_errors("TestService")(my_api_call)
        assert decorated.__doc__ == "Fetches data from API."


# ==============================================================================
# HTTPStatusError Tests
# ==============================================================================

class TestHandleApiErrorsHTTPStatusError:

    @pytest.mark.asyncio
    async def test_http_status_error_raises_exception(self):
        """HTTPStatusError is caught and re-raised as generic Exception."""
        decorated = make_decorated(
            side_effect=make_http_status_error(status_code=500)
        )
        with pytest.raises(Exception):
            await decorated()

    @pytest.mark.asyncio
    async def test_http_status_error_message_is_sanitized(self):
        """Error message does not expose raw API response details."""
        decorated = make_decorated(
            side_effect=make_http_status_error(
                status_code=500,
                body="secret internal details"
            )
        )
        with pytest.raises(Exception) as exc_info:
            await decorated()
        assert "secret internal details" not in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_http_status_error_message_contains_service_name(self):
        """Sanitized error message contains the service name."""
        decorated = make_decorated(
            service_name="EbayService",
            side_effect=make_http_status_error()
        )
        with pytest.raises(Exception) as exc_info:
            await decorated()
        assert "EbayService" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_http_status_error_is_logged(self):
        """HTTPStatusError details are logged internally."""
        decorated = make_decorated(
            service_name="EbayService",
            side_effect=make_http_status_error(status_code=401, body="Unauthorized")
        )
        with patch("core.decoration.logger") as mock_logger:
            with pytest.raises(Exception):
                await decorated()
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_http_status_error_log_contains_status_code(self):
        """Log message contains the HTTP status code."""
        decorated = make_decorated(
            service_name="EbayService",
            side_effect=make_http_status_error(status_code=403)
        )
        with patch("core.decoration.logger") as mock_logger:
            with pytest.raises(Exception):
                await decorated()
            log_message = mock_logger.error.call_args[0][0]
            assert "403" in log_message

    @pytest.mark.asyncio
    async def test_http_status_error_log_contains_response_body(self):
        """Log message contains the raw response body for debugging."""
        decorated = make_decorated(
            service_name="EbayService",
            side_effect=make_http_status_error(body="Forbidden access")
        )
        with patch("core.decoration.logger") as mock_logger:
            with pytest.raises(Exception):
                await decorated()
            log_message = mock_logger.error.call_args[0][0]
            assert "Forbidden access" in log_message


# ==============================================================================
# RequestError Tests
# ==============================================================================

class TestHandleApiErrorsRequestError:

    @pytest.mark.asyncio
    async def test_request_error_raises_exception(self):
        """RequestError is caught and re-raised as generic Exception."""
        decorated = make_decorated(
            side_effect=httpx.RequestError("Connection timeout")
        )
        with pytest.raises(Exception):
            await decorated()

    @pytest.mark.asyncio
    async def test_request_error_message_is_sanitized(self):
        """Error message does not expose raw network error details."""
        decorated = make_decorated(
            side_effect=httpx.RequestError("DNS lookup failed for internal.host")
        )
        with pytest.raises(Exception) as exc_info:
            await decorated()
        assert "DNS lookup failed" not in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_error_message_contains_service_name(self):
        """Sanitized error message contains the service name."""
        decorated = make_decorated(
            service_name="GoogleService",
            side_effect=httpx.RequestError("Timeout")
        )
        with pytest.raises(Exception) as exc_info:
            await decorated()
        assert "GoogleService" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_error_is_logged(self):
        """RequestError details are logged internally."""
        decorated = make_decorated(
            service_name="GoogleService",
            side_effect=httpx.RequestError("Connection timeout")
        )
        with patch("core.decoration.logger") as mock_logger:
            with pytest.raises(Exception):
                await decorated()
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_error_log_contains_error_details(self):
        """Log message contains the raw network error details."""
        decorated = make_decorated(
            service_name="GoogleService",
            side_effect=httpx.RequestError("Connection timeout")
        )
        with patch("core.decoration.logger") as mock_logger:
            with pytest.raises(Exception):
                await decorated()
            log_message = mock_logger.error.call_args[0][0]
            assert "Connection timeout" in log_message


# ==============================================================================
# Unexpected Exception Tests
# ==============================================================================

class TestHandleApiErrorsUnexpectedException:

    @pytest.mark.asyncio
    async def test_unexpected_exception_raises_exception(self):
        """Any unexpected exception is caught and re-raised."""
        decorated = make_decorated(
            side_effect=ValueError("Something went wrong")
        )
        with pytest.raises(Exception):
            await decorated()

    @pytest.mark.asyncio
    async def test_unexpected_exception_message_is_generic(self):
        """Generic error message shown — no internal details leaked."""
        decorated = make_decorated(
            side_effect=RuntimeError("Database connection pool exhausted")
        )
        with pytest.raises(Exception) as exc_info:
            await decorated()
        assert "Database connection pool exhausted" not in str(exc_info.value)
        assert "internal system error" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_unexpected_exception_is_logged(self):
        """Unexpected exceptions are logged with full traceback."""
        decorated = make_decorated(
            service_name="EbayService",
            side_effect=RuntimeError("Unexpected failure")
        )
        with patch("core.decoration.logger") as mock_logger:
            with pytest.raises(Exception):
                await decorated()
            mock_logger.exception.assert_called_once()

    @pytest.mark.asyncio
    async def test_unexpected_exception_log_contains_error_details(self):
        """Log message contains the raw exception details."""
        decorated = make_decorated(
            service_name="EbayService",
            side_effect=RuntimeError("Unexpected failure")
        )
        with patch("core.decoration.logger") as mock_logger:
            with pytest.raises(Exception):
                await decorated()
            log_message = mock_logger.exception.call_args[0][0]
            assert "Unexpected failure" in log_message


# ==============================================================================
# Service Name Tests
# ==============================================================================

class TestHandleApiErrorsServiceName:

    @pytest.mark.asyncio
    async def test_different_service_names_produce_different_messages(self):
        """Each service name produces a unique error message."""
        ebay_decorated = make_decorated(
            service_name="EbayService",
            side_effect=make_http_status_error()
        )
        google_decorated = make_decorated(
            service_name="GoogleService",
            side_effect=make_http_status_error()
        )
        with pytest.raises(Exception) as ebay_exc:
            await ebay_decorated()
        with pytest.raises(Exception) as google_exc:
            await google_decorated()

        assert "EbayService" in str(ebay_exc.value)
        assert "GoogleService" in str(google_exc.value)
        assert str(ebay_exc.value) != str(google_exc.value)