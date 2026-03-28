# tests/routes/test_product_route.py
import pytest
from unittest.mock import patch, AsyncMock
from exceptions.product_exceptions import ExternalAPIError

PATCH_PATH = "routes.product_route.product_services.get_products"
PRODUCT_DETAILS_PATCH_PATH = "routes.product_route.product_services.get_product_details"

MOCK_PRODUCTS = [
    {
        "id": "item-001",
        "title": "Wireless Headphones",
        "price": 99.99,
        "original_price": 149.99,
        "image_url": "https://example.com/img1.jpg"
    },
    {
        "id": "item-002",
        "title": "Bluetooth Speaker",
        "price": 49.99,
        "original_price": None,
        "image_url": "https://example.com/img2.jpg"
    }
]

MOCK_PRODUCT_DETAILS = {
    "id": "v1|123456|0",
    "title": "Wireless Headphones",
    "description": "High quality wireless headphones with ANC.",
    "price": 99.99,
    "image_url": "https://example.com/img.jpg"
}


class TestListProductsRoute:

    # -------------------------------------------------------------------------
    # Happy Path
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_list_products_returns_200(self, client):
        """Valid service response returns 200."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_PRODUCTS
            response = client.get("/product/list-products")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_products_returns_list(self, client):
        """Response body is a list."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_PRODUCTS
            response = client.get("/product/list-products")
            assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_list_products_returns_correct_count(self, client):
        """Response list has correct number of items."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_PRODUCTS
            response = client.get("/product/list-products")
            assert len(response.json()) == 2

    @pytest.mark.asyncio
    async def test_list_products_response_matches_schema(self, client):
        """Each item in response matches ProductSummaryResponse schema."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_PRODUCTS
            response = client.get("/product/list-products")
            for item in response.json():
                assert "id" in item
                assert "title" in item
                assert "price" in item
                assert "original_price" in item
                assert "image_url" in item

    @pytest.mark.asyncio
    async def test_list_products_returns_correct_data(self, client):
        """Response contains correct product data."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_PRODUCTS
            response = client.get("/product/list-products")
            first = response.json()[0]
            assert first["id"] == "item-001"
            assert first["title"] == "Wireless Headphones"
            assert first["price"] == 99.99

    @pytest.mark.asyncio
    async def test_list_products_optional_fields_nullable(self, client):
        """Optional fields like original_price can be None."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_PRODUCTS
            response = client.get("/product/list-products")
            second = response.json()[1]
            assert second["original_price"] is None

    @pytest.mark.asyncio
    async def test_list_products_empty_list_returns_200(self, client):
        """Empty product list returns 200 with empty array."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            response = client.get("/product/list-products")
            assert response.status_code == 200
            assert response.json() == []

    # -------------------------------------------------------------------------
    # Error Path
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_external_api_error_returns_502(self, client):
        """ExternalAPIError returns 502 via exception handler."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ExternalAPIError()
            response = client.get("/product/list-products")
            assert response.status_code == 502

    @pytest.mark.asyncio
    async def test_external_api_error_returns_correct_message(self, client):
        """ExternalAPIError returns user-friendly error message."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ExternalAPIError()
            response = client.get("/product/list-products")
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_response_does_not_expose_internal_error(self, client):
        """Error response never exposes internal error details."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ExternalAPIError()
            response = client.get("/product/list-products")
            body = str(response.json())
            assert "traceback" not in body.lower()
            assert "exception" not in body.lower()
            
class TestGetProductDetailsRoute:

    # -------------------------------------------------------------------------
    # Happy Path
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_valid_product_id_returns_200(self, client):
        """Valid product_id returns 200."""
        with patch(PRODUCT_DETAILS_PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_PRODUCT_DETAILS
            response = client.get("/product/v1|123456|0")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_matches_product_details_schema(self, client):
        """Response shape matches ProductDetailsResponse schema."""
        with patch(PRODUCT_DETAILS_PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_PRODUCT_DETAILS
            response = client.get("/product/v1|123456|0")
            body = response.json()
            assert "id" in body
            assert "title" in body
            assert "description" in body
            assert "price" in body
            assert "image_url" in body

    @pytest.mark.asyncio
    async def test_response_contains_correct_data(self, client):
        """Response contains correct product data."""
        with patch(PRODUCT_DETAILS_PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_PRODUCT_DETAILS
            response = client.get("/product/v1|123456|0")
            body = response.json()
            assert body["id"] == "v1|123456|0"
            assert body["title"] == "Wireless Headphones"
            assert body["description"] == \
                "High quality wireless headphones with ANC."
            assert body["price"] == 99.99

    @pytest.mark.asyncio
    async def test_image_url_can_be_none(self, client):
        """Response with None image_url is valid."""
        with patch(PRODUCT_DETAILS_PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                **MOCK_PRODUCT_DETAILS,
                "image_url": None
            }
            response = client.get("/product/v1|123456|0")
            assert response.status_code == 200
            assert response.json()["image_url"] is None

    @pytest.mark.asyncio
    async def test_product_id_passed_correctly_to_service(self, client):
        """Correct product_id is passed to service."""
        with patch(PRODUCT_DETAILS_PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_PRODUCT_DETAILS
            client.get("/product/v1|999|0")
            mock_get.assert_called_once_with("v1|999|0")

    @pytest.mark.asyncio
    async def test_different_product_ids_call_service_correctly(self, client):
        """Different product IDs produce different service calls."""
        with patch(PRODUCT_DETAILS_PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_PRODUCT_DETAILS

            client.get("/product/v1|111|0")
            first_call = mock_get.call_args[0][0]

            client.get("/product/v1|222|0")
            second_call = mock_get.call_args[0][0]

            assert first_call == "v1|111|0"
            assert second_call == "v1|222|0"
            assert first_call != second_call

    # -------------------------------------------------------------------------
    # No Auth Required
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_no_token_still_returns_200(self, client):
        """Endpoint does not require authorization header."""
        with patch(PRODUCT_DETAILS_PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_PRODUCT_DETAILS
            response = client.get(
                "/product/v1|123456|0"
                # no Authorization header
            )
            assert response.status_code == 200

    # -------------------------------------------------------------------------
    # Error Path
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_product_not_found_returns_503(self, client):
        """ExternalAPIError returns 502 via exception handler."""
        with patch(PRODUCT_DETAILS_PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ExternalAPIError()
            response = client.get("/product/v1|nonexistent|0")
            assert response.status_code == 502

    @pytest.mark.asyncio
    async def test_error_response_contains_detail(self, client):
        """Error response contains detail field."""
        with patch(PRODUCT_DETAILS_PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ExternalAPIError()
            response = client.get("/product/v1|nonexistent|0")
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_error_does_not_expose_internals(self, client):
        """Error response does not expose internal details."""
        with patch(PRODUCT_DETAILS_PATCH_PATH, new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = ExternalAPIError()
            response = client.get("/product/v1|nonexistent|0")
            body = str(response.json())
            assert "traceback" not in body.lower()
            assert "exception" not in body.lower()