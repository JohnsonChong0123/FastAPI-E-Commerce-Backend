# tests/services/ebay/test_ebay_services.py
import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from exceptions.product_exceptions import EbayAuthError
from services.ebay.ebay_services import fetch_products, fetch_single_product

AUTH_PATCH = "services.ebay.ebay_services.get_ebay_access_token"
CLIENT_PATCH = "services.ebay.ebay_services.httpx.AsyncClient"
EBAY_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
ITEM_URL = "https://api.ebay.com/buy/browse/v1/item/v1|123456|0"

MOCK_EBAY_RESPONSE = {
    "total": 2,
    "itemSummaries": [
        {
            "itemId": "item-001",
            "title": "Wireless Headphones",
            "price": {"value": "99.99", "currency": "USD"},
            "image": {"imageUrl": "https://example.com/img1.jpg"}
        },
        {
            "itemId": "item-002",
            "title": "Bluetooth Speaker",
            "price": {"value": "49.99", "currency": "USD"},
            "image": {"imageUrl": "https://example.com/img2.jpg"},
            "marketingPrice": {
                "originalPrice": {"value": "79.99", "currency": "USD"}
            }
        }
    ]
}

MOCK_ITEM_RESPONSE = {
    "itemId": "v1|123456|0",
    "title": "Wireless Headphones",
    "price": {"value": "99.99", "currency": "USD"},
    "image": {"imageUrl": "https://example.com/img.jpg"},
    "description": "Great headphones",
    "condition": "NEW"
}

def make_mock_response(status_code=200, json_data=None, text="", url=EBAY_URL):
    """Helper — builds a mock httpx response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    mock_response.text = text

    if status_code >= 400:
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=httpx.Request("GET", url),
            response=httpx.Response(status_code)
        )
    else:
        mock_response.raise_for_status.return_value = None

    return mock_response

# ==============================================================================
# Auth Failure Tests
# ==============================================================================

class TestFetchProductsAuthFailure:

    @pytest.mark.asyncio
    async def test_auth_failure_raises_exception(self):
        """
        Auth failure raises Exception.
        NOTE: EbayAuthError is swallowed by @handle_api_errors decorator.
        Caller receives generic Exception, not EbayAuthError directly.
        This documents the current behaviour — consider excluding
        EbayAuthError from decorator's catch scope.
        """
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.side_effect = Exception("Auth failed")
            with pytest.raises(Exception):
                await fetch_products()

    @pytest.mark.asyncio
    async def test_auth_failure_does_not_call_search_api(self):
        """Search API is never called when auth fails."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            with patch(CLIENT_PATCH) as mock_client:
                mock_auth.side_effect = Exception("Auth failed")
                try:
                    await fetch_products()
                except Exception:
                    pass
                mock_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_auth_failure_error_message_is_sanitized(self):
        """Auth failure error message is sanitized by decorator."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.side_effect = Exception("Auth failed")
            with pytest.raises(Exception) as exc_info:
                await fetch_products()
            assert "Auth failed" not in str(exc_info.value)


# ==============================================================================
# Happy Path Tests
# ==============================================================================

class TestFetchProductsHappyPath:

    @pytest.mark.asyncio
    async def test_returns_json_on_success(self):
        """Valid response returns parsed JSON data."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                status_code=200,
                json_data=MOCK_EBAY_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                result = await fetch_products()
                assert result == MOCK_EBAY_RESPONSE

    @pytest.mark.asyncio
    async def test_returns_item_summaries(self):
        """Response contains itemSummaries list."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                status_code=200,
                json_data=MOCK_EBAY_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                result = await fetch_products()
                assert "itemSummaries" in result
                assert len(result["itemSummaries"]) == 2

    @pytest.mark.asyncio
    async def test_raise_for_status_is_called(self):
        """raise_for_status() is called on every response."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                status_code=200,
                json_data=MOCK_EBAY_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                await fetch_products()
                mock_response.raise_for_status.assert_called_once()


# ==============================================================================
# Request Construction Tests
# ==============================================================================

class TestFetchProductsRequestConstruction:

    @pytest.mark.asyncio
    async def test_correct_url_is_called(self):
        """Correct eBay Browse API URL is used."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                status_code=200,
                json_data=MOCK_EBAY_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.get = mock_get
                await fetch_products()
                assert mock_get.call_args[0][0] == \
                    "https://api.ebay.com/buy/browse/v1/item_summary/search"

    @pytest.mark.asyncio
    async def test_bearer_token_in_authorization_header(self):
        """Authorization header contains Bearer token."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                status_code=200,
                json_data=MOCK_EBAY_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.get = mock_get
                await fetch_products()
                headers = mock_get.call_args[1]["headers"]
                assert headers["Authorization"] == "Bearer valid.token"

    @pytest.mark.asyncio
    async def test_correct_query_in_params(self):
        """Correct q param is sent."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                status_code=200,
                json_data=MOCK_EBAY_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.get = mock_get
                await fetch_products()
                params = mock_get.call_args[1]["params"]
                assert params["q"] == "laptop"
                
    @pytest.mark.asyncio
    async def test_correct_sort_in_params(self):
        """Correct sort param is sent."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                status_code=200,
                json_data=MOCK_EBAY_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.get = mock_get
                await fetch_products()
                params = mock_get.call_args[1]["params"]
                assert params["sort"] == "newlyListed"
                
    @pytest.mark.asyncio
    async def test_correct_filter_in_params(self):
        """Correct filter param is sent."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                status_code=200,
                json_data=MOCK_EBAY_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.get = mock_get
                await fetch_products()
                params = mock_get.call_args[1]["params"]
                assert params["filter"] == "conditions:{NEW}"

    @pytest.mark.asyncio
    async def test_correct_limit_in_params(self):
        """Correct limit param is sent."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                status_code=200,
                json_data=MOCK_EBAY_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.get = mock_get
                await fetch_products()
                params = mock_get.call_args[1]["params"]
                assert params["limit"] == 100

    @pytest.mark.asyncio
    async def test_content_type_is_json(self):
        """Content-Type header is application/json."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                status_code=200,
                json_data=MOCK_EBAY_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.get = mock_get
                await fetch_products()
                headers = mock_get.call_args[1]["headers"]
                assert headers["Content-Type"] == "application/json"


# ==============================================================================
# Error Path Tests — decorator transforms exceptions
# ==============================================================================

class TestFetchProductsErrorPath:

    @pytest.mark.asyncio
    async def test_404_raises_sanitized_exception(self):
        """404 raises sanitized Exception via decorator."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(status_code=404)
            with patch(CLIENT_PATCH) as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                with pytest.raises(Exception) as exc_info:
                    await fetch_products()
                assert "eBay-Search" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_500_raises_sanitized_exception(self):
        """500 raises sanitized Exception via decorator."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(status_code=500)
            with patch(CLIENT_PATCH) as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                with pytest.raises(Exception) as exc_info:
                    await fetch_products()
                assert "eBay-Search" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_network_error_raises_sanitized_exception(self):
        """Network error raises sanitized Exception via decorator."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            with patch(CLIENT_PATCH) as mock_client:
                request = httpx.Request(
                    "GET",
                    "https://api.ebay.com/buy/browse/v1/item_summary/search"
                )
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.ConnectTimeout("Timeout", request=request)
                )
                with pytest.raises(Exception) as exc_info:
                    await fetch_products()
                assert "eBay-Search" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_message_does_not_expose_token(self):
        """Error messages never expose the Bearer token."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "my.secret.token"
            mock_response = make_mock_response(status_code=401)
            with patch(CLIENT_PATCH) as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                with pytest.raises(Exception) as exc_info:
                    await fetch_products()
                assert "my.secret.token" not in str(exc_info.value)


# ==============================================================================
# Critical Gap — EbayAuthError swallowed by decorator
# ==============================================================================

class TestFetchProductsEbayAuthErrorGap:

    @pytest.mark.asyncio
    async def test_ebay_auth_error_swallowed_by_decorator(self):
        """
        DOCUMENTS CRITICAL GAP:
        EbayAuthError raised inside fetch_products is caught by
        @handle_api_errors decorator and becomes a generic Exception.

        Caller cannot distinguish auth failure from other errors.

        Fix option 1 — exclude EbayAuthError from decorator:
            except Exception as e:
                if isinstance(e, EbayAuthError):
                    raise
                ...

        Fix option 2 — remove try/except inside fetch_products
        and let decorator handle auth errors directly.
        """
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.side_effect = Exception("Auth failed")
            with pytest.raises(Exception) as exc_info:
                await fetch_products()
            # EbayAuthError is NOT raised — generic Exception instead
            assert not isinstance(exc_info.value, EbayAuthError)
            assert "internal system error" in str(exc_info.value).lower()
            
# ==============================================================================
# Auth Failure Tests
# ==============================================================================

class TestFetchSingleProductAuthFailure:

    @pytest.mark.asyncio
    async def test_auth_failure_raises_exception(self):
        """Auth failure raises Exception via decorator."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.side_effect = Exception("Auth failed")
            with pytest.raises(Exception):
                await fetch_single_product("v1|123456|0")

    @pytest.mark.asyncio
    async def test_auth_failure_does_not_call_item_api(self):
        """Item API is never called when auth fails."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            with patch(CLIENT_PATCH) as mock_client:
                mock_auth.side_effect = Exception("Auth failed")
                try:
                    await fetch_single_product("v1|123456|0")
                except Exception:
                    pass
                mock_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_auth_error_message_is_sanitized(self):
        """Auth failure error message is sanitized by decorator."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.side_effect = Exception("Auth failed")
            with pytest.raises(Exception) as exc_info:
                await fetch_single_product("v1|123456|0")
            assert "Auth failed" not in str(exc_info.value)


# ==============================================================================
# Happy Path Tests
# ==============================================================================

class TestFetchSingleProductHappyPath:

    @pytest.mark.asyncio
    async def test_returns_item_json(self):
        """Valid response returns parsed item JSON."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                url=ITEM_URL,
                status_code=200,
                json_data=MOCK_ITEM_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                result = await fetch_single_product("v1|123456|0")
                assert result == MOCK_ITEM_RESPONSE

    @pytest.mark.asyncio
    async def test_returns_correct_item_id(self):
        """Returned item has correct itemId."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                url=ITEM_URL,
                status_code=200,
                json_data=MOCK_ITEM_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                result = await fetch_single_product("v1|123456|0")
                assert result["itemId"] == "v1|123456|0"

    @pytest.mark.asyncio
    async def test_raise_for_status_is_called(self):
        """raise_for_status() is called for non-404 responses."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                url=ITEM_URL,
                status_code=200,
                json_data=MOCK_ITEM_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                await fetch_single_product("v1|123456|0")
                mock_response.raise_for_status.assert_called_once()


# ==============================================================================
# Request Construction Tests
# ==============================================================================

class TestFetchSingleProductRequestConstruction:

    @pytest.mark.asyncio
    async def test_correct_url_with_item_id(self):
        """Correct eBay item URL is constructed with item_id."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                url=ITEM_URL,
                status_code=200,
                json_data=MOCK_ITEM_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.get = mock_get
                await fetch_single_product("v1|123456|0")
                assert mock_get.call_args[0][0] == \
                    "https://api.ebay.com/buy/browse/v1/item/v1|123456|0"

    @pytest.mark.asyncio
    async def test_different_item_ids_produce_different_urls(self):
        """Different item_ids produce different request URLs."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                url=ITEM_URL,
                status_code=200,
                json_data=MOCK_ITEM_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.get = mock_get

                await fetch_single_product("v1|111|0")
                url_1 = mock_get.call_args[0][0]

                await fetch_single_product("v1|222|0")
                url_2 = mock_get.call_args[0][0]

                assert url_1 != url_2
                assert "v1|111|0" in url_1
                assert "v1|222|0" in url_2

    @pytest.mark.asyncio
    async def test_bearer_token_in_authorization_header(self):
        """Authorization header contains Bearer token."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                url=ITEM_URL,
                status_code=200,
                json_data=MOCK_ITEM_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.get = mock_get
                await fetch_single_product("v1|123456|0")
                headers = mock_get.call_args[1]["headers"]
                assert headers["Authorization"] == "Bearer valid.token"

    @pytest.mark.asyncio
    async def test_content_type_is_json(self):
        """Content-Type header is application/json."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(
                url=ITEM_URL,
                status_code=200,
                json_data=MOCK_ITEM_RESPONSE
            )
            with patch(CLIENT_PATCH) as mock_client:
                mock_get = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.get = mock_get
                await fetch_single_product("v1|123456|0")
                headers = mock_get.call_args[1]["headers"]
                assert headers["Content-Type"] == "application/json"
                
# ==============================================================================
# Error Path Tests — decorator transforms exceptions
# ==============================================================================

class TestFetchSingleProductErrorPath:

    @pytest.mark.asyncio
    async def test_401_raises_sanitized_exception(self):
        """401 raises sanitized Exception via decorator."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(status_code=401, url=ITEM_URL)
            with patch(CLIENT_PATCH) as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                with pytest.raises(Exception) as exc_info:
                    await fetch_single_product("v1|123456|0")
                assert "eBay-Item-Detail" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_500_raises_sanitized_exception(self):
        """500 raises sanitized Exception via decorator."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            mock_response = make_mock_response(status_code=500, url=ITEM_URL)
            with patch(CLIENT_PATCH) as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                with pytest.raises(Exception) as exc_info:
                    await fetch_single_product("v1|123456|0")
                assert "eBay-Item-Detail" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_network_error_raises_sanitized_exception(self):
        """Network error raises sanitized Exception via decorator."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid.token"
            with patch(CLIENT_PATCH) as mock_client:
                request = httpx.Request(
                    "GET",
                    "https://api.ebay.com/buy/browse/v1/item/v1|123456|0"
                )
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.ConnectTimeout("Timeout", request=request)
                )
                with pytest.raises(Exception) as exc_info:
                    await fetch_single_product("v1|123456|0")
                assert "eBay-Item-Detail" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_does_not_expose_token(self):
        """Error messages never expose the Bearer token."""
        with patch(AUTH_PATCH, new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "my.secret.token"
            mock_response = make_mock_response(status_code=401, url=ITEM_URL)
            with patch(CLIENT_PATCH) as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                with pytest.raises(Exception) as exc_info:
                    await fetch_single_product("v1|123456|0")
                assert "my.secret.token" not in str(exc_info.value)