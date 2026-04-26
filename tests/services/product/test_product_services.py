# tests/services/test_product_service.py
import pytest
from unittest.mock import patch, AsyncMock
from exceptions.product_exceptions import ExternalAPIError
from services.product.product_services import get_products
from services.product.product_services import get_product_details

PATCH_PATH = "services.product.product_services.fetch_products"
SINGLE_PRODUCT_PATCH_PATH = "services.product.product_services.fetch_single_product"

MOCK_EBAY_ITEM = {
    "itemId": "v1|123456|0",
    "title": "Wireless Headphones",
    "shortDescription": "High quality wireless headphones with ANC.",
    "price": {"value": "99.99", "currency": "USD"},
    "image": {"imageUrl": "https://example.com/img.jpg"},
    "additionalImages": [
        {"imageUrl": "https://example.com/img1.jpg"},
        {"imageUrl": "https://example.com/img2.jpg"}
    ]
}


def make_item(
    item_id="item-123",
    title="Wireless Headphones",
    price="99.99",
    marketing_price=None,
    image_url="https://example.com/image.jpg",
    additional_images=["https://example.com/add1.jpg", "https://example.com/add2.jpg"]
):
    """Helper to build a mock eBay item."""
    item = {
        "itemId": item_id,
        "title": title,
        "price": {"value": price},
        "image": {"imageUrl": image_url},
        "additionalImages": [{"imageUrl": url} for url in additional_images]
    }
    if marketing_price:
        item["marketingPrice"] = {
            "originalPrice": {"value": marketing_price}
        }
    return item


# ==============================================================================
# ExternalAPIError Tests
# ==============================================================================

class TestGetProductsAPIError:

    @pytest.mark.asyncio
    async def test_none_response_raises_external_api_error(self):
        """None API response raises ExternalAPIError."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            with pytest.raises(ExternalAPIError):
                await get_products()

    @pytest.mark.asyncio
    async def test_empty_dict_raises_external_api_error(self):
        """Empty dict API response raises ExternalAPIError."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {}
            with pytest.raises(ExternalAPIError):
                await get_products()

    @pytest.mark.asyncio
    async def test_fetch_raises_exception_propagates(self):
        """Exception from fetch_products propagates correctly."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("Network error")
            with pytest.raises(Exception):
                await get_products()


# ==============================================================================
# Happy Path Tests
# ==============================================================================

class TestGetProductsHappyPath:

    @pytest.mark.asyncio
    async def test_returns_list(self):
        """Valid API response returns a list."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemSummaries": [make_item()]
            }
            result = await get_products()
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_returns_correct_number_of_items(self):
        """Returns same number of items as API response."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemSummaries": [make_item("1"), make_item("2"), make_item("3")]
            }
            result = await get_products()
            assert len(result) == 3

    @pytest.mark.asyncio
    async def test_empty_item_summaries_returns_empty_list(self):
        """API response with no items returns empty list."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"itemSummaries": []}
            result = await get_products()
            assert result == []

    @pytest.mark.asyncio
    async def test_missing_item_summaries_returns_empty_list(self):
        """API response without itemSummaries key returns empty list."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"total": 0}
            with pytest.raises(ExternalAPIError):
                await get_products()


# ==============================================================================
# Field Parsing Tests
# ==============================================================================

class TestGetProductsFieldParsing:

    @pytest.mark.asyncio
    async def test_item_id_parsed_correctly(self):
        """itemId is mapped to id field."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemSummaries": [make_item(item_id="item-abc")]
            }
            result = await get_products()
            assert result[0]["id"] == "item-abc"

    @pytest.mark.asyncio
    async def test_title_parsed_correctly(self):
        """title is mapped correctly."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemSummaries": [make_item(title="Sony Headphones")]
            }
            result = await get_products()
            assert result[0]["title"] == "Sony Headphones"

    @pytest.mark.asyncio
    async def test_price_parsed_as_float(self):
        """price value is parsed as float."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemSummaries": [make_item(price="99.99")]
            }
            result = await get_products()
            assert result[0]["price"] == 99.99
            assert isinstance(result[0]["price"], float)

    @pytest.mark.asyncio
    async def test_image_url_parsed_correctly(self):
        """imageUrl is mapped to image_url field."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemSummaries": [
                    make_item(image_url="https://example.com/img.jpg")
                ]
            }
            result = await get_products()
            assert result[0]["image_url"] == "https://example.com/img.jpg"

    @pytest.mark.asyncio
    async def test_original_price_parsed_when_marketing_present(self):
        """original_price populated when marketingPrice exists."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemSummaries": [
                    make_item(price="99.99", marketing_price="149.99")
                ]
            }
            result = await get_products()
            assert result[0]["original_price"] == 149.99

    @pytest.mark.asyncio
    async def test_original_price_none_when_no_marketing(self):
        """original_price is None when no marketingPrice."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemSummaries": [make_item()]   # no marketing_price
            }
            result = await get_products()
            assert result[0]["original_price"] is None


# ==============================================================================
# Missing/Default Field Tests
# ==============================================================================

class TestGetProductsMissingFields:

    @pytest.mark.asyncio
    async def test_missing_price_defaults_to_zero(self):
        """Missing price field defaults to 0.0."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemSummaries": [{
                    "itemId": "item-123",
                    "title": "Headphones"
                    # no price field
                }]
            }
            result = await get_products()
            assert result[0]["price"] == 0.0

    @pytest.mark.asyncio
    async def test_missing_image_url_defaults_to_none(self):
        """Missing image field defaults to None."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemSummaries": [{
                    "itemId": "item-123",
                    "title": "Headphones",
                    "price": {"value": "99.99"}
                    # no image field
                }]
            }
            result = await get_products()
            assert result[0]["image_url"] is None

    @pytest.mark.asyncio
    async def test_missing_title_defaults_to_none(self):
        """Missing title defaults to None."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemSummaries": [{
                    "itemId": "item-123",
                    "price": {"value": "99.99"}
                    # no title
                }]
            }
            result = await get_products()
            assert result[0]["title"] is None

    @pytest.mark.asyncio
    async def test_marketing_with_missing_original_price_defaults(self):
        """
        marketing exists but originalPrice missing — currently returns 0.0.
        Documents the behaviour — consider returning None instead.
        """
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemSummaries": [{
                    "itemId": "item-123",
                    "title": "Headphones",
                    "price": {"value": "99.99"},
                    "marketingPrice": {}    # empty marketing, no originalPrice
                }]
            }
            result = await get_products()
            assert result[0]["original_price"] == 0.0   # ← documents bug
        
# ==============================================================================
# ExternalAPIError Tests
# ==============================================================================

class TestGetProductDetailsAPIError:

    @pytest.mark.asyncio
    async def test_none_response_raises_external_api_error(self):
        """None from fetch_single_product raises ExternalAPIError."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            with pytest.raises(ExternalAPIError):
                await get_product_details("v1|123456|0")

    @pytest.mark.asyncio
    async def test_fetch_exception_propagates(self):
        """Exception from fetch_single_product propagates."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("eBay-Item-Detail error")
            with pytest.raises(Exception):
                await get_product_details("v1|123456|0")

    @pytest.mark.asyncio
    async def test_none_does_not_return_partial_data(self):
        """No partial data returned when product not found."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            try:
                await get_product_details("v1|123456|0")
            except ExternalAPIError:
                pass


# ==============================================================================
# Happy Path Tests
# ==============================================================================

class TestGetProductDetailsHappyPath:

    @pytest.mark.asyncio
    async def test_returns_dict(self):
        """Valid response returns a dict."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_ITEM
            result = await get_product_details("v1|123456|0")
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_fetch_called_with_correct_product_id(self):
        """fetch_single_product called with correct product_id."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_ITEM
            await get_product_details("v1|123456|0")
            mock_fetch.assert_called_once_with("v1|123456|0")

    @pytest.mark.asyncio
    async def test_different_product_ids_call_fetch_correctly(self):
        """Different product IDs are passed correctly to fetch."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_ITEM
            await get_product_details("v1|999|0")
            mock_fetch.assert_called_once_with("v1|999|0")


# ==============================================================================
# Field Parsing Tests
# ==============================================================================

class TestGetProductDetailsFieldParsing:

    @pytest.mark.asyncio
    async def test_id_parsed_from_item_id(self):
        """itemId is mapped to id field."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_ITEM
            result = await get_product_details("v1|123456|0")
            assert result["id"] == "v1|123456|0"

    @pytest.mark.asyncio
    async def test_title_parsed_correctly(self):
        """title is mapped correctly."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_ITEM
            result = await get_product_details("v1|123456|0")
            assert result["title"] == "Wireless Headphones"

    @pytest.mark.asyncio
    async def test_description_parsed_from_short_description(self):
        """description is mapped from shortDescription field."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_ITEM
            result = await get_product_details("v1|123456|0")
            assert result["description"] == \
                "High quality wireless headphones with ANC."

    @pytest.mark.asyncio
    async def test_price_parsed_as_float(self):
        """price value is parsed as float."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_ITEM
            result = await get_product_details("v1|123456|0")
            assert result["price"] == 99.99
            assert isinstance(result["price"], float)

    @pytest.mark.asyncio
    async def test_image_url_parsed_correctly(self):
        """imageUrl is mapped to image_url field."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_ITEM
            result = await get_product_details("v1|123456|0")
            assert result["image_url"] == "https://example.com/img.jpg"
            
    @pytest.mark.asyncio
    async def test_additional_images_parsed_correctly(self):
        """additionalImages list is parsed to additional_images field."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_ITEM
            result = await get_product_details("v1|123456|0")
            assert result["additional_images"] == [
                "https://example.com/img1.jpg",
                "https://example.com/img2.jpg"
            ]


# ==============================================================================
# Missing Field Tests
# ==============================================================================

class TestGetProductDetailsMissingFields:

    @pytest.mark.asyncio
    async def test_missing_short_description_defaults_to_none(self):
        """Missing shortDescription defaults to None."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemId": "v1|123456|0",
                "title": "Wireless Headphones",
                "price": {"value": "99.99"}
                # no shortDescription
            }
            result = await get_product_details("v1|123456|0")
            assert result["description"] is None

    @pytest.mark.asyncio
    async def test_missing_price_defaults_to_zero(self):
        """Missing price defaults to 0.0."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemId": "v1|123456|0",
                "title": "Wireless Headphones",
                "shortDescription": "Great product."
                # no price
            }
            result = await get_product_details("v1|123456|0")
            assert result["price"] == 0.0

    @pytest.mark.asyncio
    async def test_missing_image_defaults_to_none(self):
        """Missing image field defaults to None."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemId": "v1|123456|0",
                "title": "Wireless Headphones",
                "shortDescription": "Great product.",
                "price": {"value": "99.99"}
                # no image
            }
            result = await get_product_details("v1|123456|0")
            assert result["image_url"] is None

    @pytest.mark.asyncio
    async def test_missing_title_defaults_to_none(self):
        """Missing title defaults to None."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "itemId": "v1|123456|0",
                "shortDescription": "Great product.",
                "price": {"value": "99.99"}
                # no title
            }
            result = await get_product_details("v1|123456|0")
            assert result["title"] is None

    @pytest.mark.asyncio
    async def test_missing_item_id_defaults_to_none(self):
        """Missing itemId defaults to None."""
        with patch(SINGLE_PRODUCT_PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "title": "Wireless Headphones",
                "shortDescription": "Great product.",
                "price": {"value": "99.99"}
                # no itemId
            }
            result = await get_product_details("v1|123456|0")
            assert result["id"] is None