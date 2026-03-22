# tests/services/ebay/test_ebay_auth.py
import pytest
import base64
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from core.config import settings
from services.ebay.ebay_auth import get_ebay_access_token


PATCH_PATH = "services.ebay.ebay_auth.httpx.AsyncClient"


def make_mock_response(status_code=200, json_data=None, text=""):
    """Helper — builds a mock httpx response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    mock_response.text = text

    if status_code >= 400:
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=httpx.Request("POST", "https://api.ebay.com/identity/v1/oauth2/token"),
            response=httpx.Response(status_code, text=text)
        )
    else:
        mock_response.raise_for_status.return_value = None

    return mock_response


# ==============================================================================
# Happy Path Tests
# ==============================================================================

class TestGetEbayAccessTokenHappyPath:

    @pytest.mark.asyncio
    async def test_valid_credentials_returns_access_token(self):
        """Valid credentials return access token string."""
        mock_response = make_mock_response(
            status_code=200,
            json_data={"access_token": "ebay.access.token.123"}
        )
        with patch(PATCH_PATH) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            result = await get_ebay_access_token()
            assert result == "ebay.access.token.123"

    @pytest.mark.asyncio
    async def test_returns_non_empty_string(self):
        """Returned token is a non-empty string."""
        mock_response = make_mock_response(
            status_code=200,
            json_data={"access_token": "ebay.access.token.123"}
        )
        with patch(PATCH_PATH) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            result = await get_ebay_access_token()
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_raise_for_status_is_called(self):
        """raise_for_status() is called on every response."""
        mock_response = make_mock_response(
            status_code=200,
            json_data={"access_token": "token"}
        )
        with patch(PATCH_PATH) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            await get_ebay_access_token()
            mock_response.raise_for_status.assert_called_once()


# ==============================================================================
# Request Construction Tests
# ==============================================================================

class TestGetEbayAccessTokenRequestConstruction:

    @pytest.mark.asyncio
    async def test_correct_url_is_called(self):
        """Correct eBay OAuth URL is used."""
        mock_response = make_mock_response(
            status_code=200,
            json_data={"access_token": "token"}
        )
        with patch(PATCH_PATH) as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            await get_ebay_access_token()
            assert mock_post.call_args[0][0] == \
                "https://api.ebay.com/identity/v1/oauth2/token"

    @pytest.mark.asyncio
    async def test_correct_grant_type_sent(self):
        """client_credentials grant type is sent."""
        mock_response = make_mock_response(
            status_code=200,
            json_data={"access_token": "token"}
        )
        with patch(PATCH_PATH) as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            await get_ebay_access_token()
            data = mock_post.call_args[1]["data"]
            assert data["grant_type"] == "client_credentials"

    @pytest.mark.asyncio
    async def test_correct_scope_sent(self):
        """Correct eBay API scope is sent."""
        mock_response = make_mock_response(
            status_code=200,
            json_data={"access_token": "token"}
        )
        with patch(PATCH_PATH) as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            await get_ebay_access_token()
            data = mock_post.call_args[1]["data"]
            assert data["scope"] == "https://api.ebay.com/oauth/api_scope"

    @pytest.mark.asyncio
    async def test_authorization_header_uses_basic_auth(self):
        """Authorization header uses Basic auth scheme."""
        mock_response = make_mock_response(
            status_code=200,
            json_data={"access_token": "token"}
        )
        with patch(PATCH_PATH) as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            await get_ebay_access_token()
            headers = mock_post.call_args[1]["headers"]
            assert headers["Authorization"].startswith("Basic ")

    @pytest.mark.asyncio
    async def test_authorization_header_encodes_credentials_correctly(self):
        """Base64 encoded credentials are correct."""
        mock_response = make_mock_response(
            status_code=200,
            json_data={"access_token": "token"}
        )
        with patch(PATCH_PATH) as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            await get_ebay_access_token()
            headers = mock_post.call_args[1]["headers"]
            b64_part = headers["Authorization"].replace("Basic ", "")
            decoded = base64.b64decode(b64_part).decode()
            assert decoded == \
                f"{settings.EBAY_CLIENT_ID}:{settings.EBAY_CLIENT_SECRET}"

    @pytest.mark.asyncio
    async def test_content_type_is_form_urlencoded(self):
        """Content-Type is application/x-www-form-urlencoded."""
        mock_response = make_mock_response(
            status_code=200,
            json_data={"access_token": "token"}
        )
        with patch(PATCH_PATH) as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            await get_ebay_access_token()
            headers = mock_post.call_args[1]["headers"]
            assert headers["Content-Type"] == \
                "application/x-www-form-urlencoded"


# ==============================================================================
# Error Path Tests — decorator transforms exceptions
# ==============================================================================

class TestGetEbayAccessTokenErrorPath:

    @pytest.mark.asyncio
    async def test_401_raises_sanitized_exception(self):
        """401 response raises sanitized Exception via decorator."""
        mock_response = make_mock_response(status_code=401, text="Unauthorized")
        with patch(PATCH_PATH) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            with pytest.raises(Exception) as exc_info:
                await get_ebay_access_token()
            # decorator message, not raw httpx error
            assert "eBay-OAuth" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_401_error_message_is_sanitized(self):
        """401 error message does not expose raw response body."""
        mock_response = make_mock_response(
            status_code=401,
            text=f"Invalid client: {settings.EBAY_CLIENT_SECRET}"
        )
        with patch(PATCH_PATH) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            with pytest.raises(Exception) as exc_info:
                await get_ebay_access_token()
            assert settings.EBAY_CLIENT_SECRET not in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_500_raises_sanitized_exception(self):
        """500 response raises sanitized Exception via decorator."""
        mock_response = make_mock_response(
            status_code=500,
            text="Internal Server Error"
        )
        with patch(PATCH_PATH) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            with pytest.raises(Exception):
                await get_ebay_access_token()

    @pytest.mark.asyncio
    async def test_network_error_raises_sanitized_exception(self):
        """Network error raises sanitized Exception via decorator."""
        with patch(PATCH_PATH) as mock_client:
            request = httpx.Request(
                "POST",
                "https://api.ebay.com/identity/v1/oauth2/token"
            )
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.ConnectTimeout("Timeout", request=request)
            )
            with pytest.raises(Exception) as exc_info:
                await get_ebay_access_token()
            assert "eBay-OAuth" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_missing_token_raises_sanitized_exception(self):
        """
        200 response with no access_token raises sanitized Exception.
        ValueError is caught by decorator → generic error message.
        """
        mock_response = make_mock_response(
            status_code=200,
            json_data={}    # no access_token key
        )
        with patch(PATCH_PATH) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            with pytest.raises(Exception) as exc_info:
                await get_ebay_access_token()
            assert "internal system error" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_raw_credentials_not_in_any_exception_message(self):
        """No exception message ever exposes raw credentials."""
        mock_response = make_mock_response(status_code=401, text="Unauthorized")
        with patch(PATCH_PATH) as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            with pytest.raises(Exception) as exc_info:
                await get_ebay_access_token()
            assert settings.EBAY_CLIENT_SECRET not in str(exc_info.value)
            assert settings.EBAY_CLIENT_ID not in str(exc_info.value)