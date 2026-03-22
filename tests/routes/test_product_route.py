# tests/routes/test_product_route.py
import pytest
from unittest.mock import patch, AsyncMock
from exceptions.product_exceptions import ExternalAPIError


PATCH_PATH = "routes.product_route.product_services.get_products"

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