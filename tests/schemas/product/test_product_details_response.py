# tests/schemas/test_product_details_response.py
import pytest
from unittest.mock import MagicMock
from pydantic import ValidationError
from schemas.product.product_details_response import (
    ProductDetailsResponse,
    Price,
    ShippingOption,
    ShippingCost,
    LocalizedAspect,
)


# ==============================================================================
# HELPERS
# ==============================================================================

def make_price(**overrides):
    """Helper — builds valid Price data."""
    data = {"value": 99.99, "currency": "USD"}
    data.update(overrides)
    return data


def make_shipping_option(**overrides):
    """Helper — builds valid ShippingOption data."""
    data = {
        "shippingServiceCode": "UPS_GROUND",
        "type": "FIXED",
        "shippingCost": {"value": 5.99, "currency": "USD"},
        "additionalShippingCostPerUnit": {"value": 1.00, "currency": "USD"},
        "shippingCostType": "FLAT_RATE"
    }
    data.update(overrides)
    return data


def make_localized_aspect(**overrides):
    """Helper — builds valid LocalizedAspect data."""
    data = {"type": "DESCRIPTIVE", "name": "Color", "value": "Black"}
    data.update(overrides)
    return data


def make_product_data(**overrides):
    """Helper — builds valid ProductDetailsResponse data."""
    data = {
        "id": "v1|123456|0",
        "title": "Wireless Headphones",
        "description": "High quality wireless headphones with ANC.",
        "price": make_price(),
        "image_url": "https://example.com/img.jpg",
        "additional_images": [
            "https://example.com/img1.jpg",
            "https://example.com/img2.jpg"
        ],
        "localized_aspects": [make_localized_aspect()],
        "shipping_options": [make_shipping_option()]
    }
    data.update(overrides)
    return data


# ==============================================================================
# Price Model Tests
# ==============================================================================

class TestPriceModel:

    def test_valid_price_with_currency(self):
        """Price with value and currency passes."""
        price = Price(value=99.99, currency="USD")
        assert price.value == 99.99
        assert price.currency == "USD"

    def test_price_currency_optional(self):
        """Price without currency is valid."""
        price = Price(value=99.99)
        assert price.currency is None

    def test_price_coerces_int_to_float(self):
        """Integer price value coerced to float."""
        price = Price(value=100, currency="USD")
        assert isinstance(price.value, float)

    def test_price_missing_value_raises_error(self):
        """Missing value raises ValidationError."""
        with pytest.raises(ValidationError):
            Price(currency="USD")

    def test_price_invalid_value_raises_error(self):
        """Non-numeric value raises ValidationError."""
        with pytest.raises(ValidationError):
            Price(value="free", currency="USD")


# ==============================================================================
# ShippingCost Model Tests
# ==============================================================================

class TestShippingCostModel:

    def test_valid_shipping_cost(self):
        """Valid shipping cost passes."""
        cost = ShippingCost(value=5.99, currency="USD")
        assert cost.value == 5.99
        assert cost.currency == "USD"

    def test_shipping_cost_rounds_to_two_decimal_places(self):
        """ShippingCost serializes value to 2 decimal places."""
        cost = ShippingCost(value=5.999, currency="USD")
        serialized = cost.model_dump()
        assert serialized["value"] == 6.00

    def test_shipping_cost_rounds_half_up(self):
        """ShippingCost uses ROUND_HALF_UP rounding."""
        cost = ShippingCost(value=5.555, currency="USD")
        serialized = cost.model_dump()
        assert serialized["value"] == 5.56

    def test_shipping_cost_missing_value_raises_error(self):
        """Missing value raises ValidationError."""
        with pytest.raises(ValidationError):
            ShippingCost(currency="USD")

    def test_shipping_cost_missing_currency_raises_error(self):
        """Missing currency raises ValidationError."""
        with pytest.raises(ValidationError):
            ShippingCost(value=5.99)


# ==============================================================================
# ShippingOption Model Tests
# ==============================================================================

class TestShippingOptionModel:

    def test_valid_full_shipping_option(self):
        """All fields provided with valid data passes."""
        option = ShippingOption(**make_shipping_option())
        assert option.shippingServiceCode == "UPS_GROUND"
        assert option.type == "FIXED"
        assert option.shippingCost.value == 5.99

    def test_all_fields_optional(self):
        """ShippingOption with no fields is valid."""
        option = ShippingOption()
        assert option.shippingServiceCode is None
        assert option.type is None
        assert option.shippingCost is None
        assert option.additionalShippingCostPerUnit is None
        assert option.shippingCostType is None

    def test_shipping_cost_is_nested_model(self):
        """shippingCost is a ShippingCost instance."""
        option = ShippingOption(**make_shipping_option())
        assert isinstance(option.shippingCost, ShippingCost)

    def test_additional_shipping_cost_is_nested_model(self):
        """additionalShippingCostPerUnit is a ShippingCost instance."""
        option = ShippingOption(**make_shipping_option())
        assert isinstance(option.additionalShippingCostPerUnit, ShippingCost)


# ==============================================================================
# LocalizedAspect Model Tests
# ==============================================================================

class TestLocalizedAspectModel:

    def test_valid_localized_aspect(self):
        """All fields provided passes."""
        aspect = LocalizedAspect(**make_localized_aspect())
        assert aspect.type == "DESCRIPTIVE"
        assert aspect.name == "Color"
        assert aspect.value == "Black"

    def test_all_fields_optional(self):
        """LocalizedAspect with no fields is valid."""
        aspect = LocalizedAspect()
        assert aspect.type is None
        assert aspect.name is None
        assert aspect.value is None

    def test_partial_fields_valid(self):
        """LocalizedAspect with only some fields is valid."""
        aspect = LocalizedAspect(name="Color")
        assert aspect.name == "Color"
        assert aspect.type is None


# ==============================================================================
# ProductDetailsResponse Valid Data Tests
# ==============================================================================

class TestProductDetailsResponseValidData:

    def test_valid_full_data(self):
        """All fields provided with valid data passes."""
        data = ProductDetailsResponse(**make_product_data())
        assert data.id == "v1|123456|0"
        assert data.title == "Wireless Headphones"
        assert data.description == "High quality wireless headphones with ANC."
        assert isinstance(data.price, Price)
        assert data.price.value == 99.99
        assert data.image_url == "https://example.com/img.jpg"

    def test_price_is_nested_price_model(self):
        """price field is a Price instance."""
        data = ProductDetailsResponse(**make_product_data())
        assert isinstance(data.price, Price)
        assert data.price.currency == "USD"

    def test_image_url_defaults_to_none(self):
        """image_url defaults to None when not provided."""
        data = ProductDetailsResponse(**make_product_data(image_url=None))
        assert data.image_url is None

    def test_valid_without_image_url(self):
        """ProductDetailsResponse is valid without image_url."""
        product_data = make_product_data()
        del product_data["image_url"]
        data = ProductDetailsResponse(**product_data)
        assert data.image_url is None

    def test_additional_images_defaults_to_none(self):
        """additional_images defaults to None when not provided."""
        product_data = make_product_data()
        del product_data["additional_images"]
        data = ProductDetailsResponse(**product_data)
        assert data.additional_images is None

    def test_additional_images_populated_correctly(self):
        """additional_images list is populated correctly."""
        data = ProductDetailsResponse(**make_product_data())
        assert len(data.additional_images) == 2
        assert "https://example.com/img1.jpg" in data.additional_images

    def test_localized_aspects_defaults_to_empty_list(self):
        """localized_aspects defaults to empty list."""
        product_data = make_product_data()
        del product_data["localized_aspects"]
        data = ProductDetailsResponse(**product_data)
        assert data.localized_aspects == []

    def test_localized_aspects_populated_correctly(self):
        """localized_aspects list contains LocalizedAspect instances."""
        data = ProductDetailsResponse(**make_product_data())
        assert len(data.localized_aspects) == 1
        assert isinstance(data.localized_aspects[0], LocalizedAspect)
        assert data.localized_aspects[0].name == "Color"

    def test_shipping_options_defaults_to_empty_list(self):
        """shipping_options defaults to empty list."""
        product_data = make_product_data()
        del product_data["shipping_options"]
        data = ProductDetailsResponse(**product_data)
        assert data.shipping_options == []

    def test_shipping_options_populated_correctly(self):
        """shipping_options list contains ShippingOption instances."""
        data = ProductDetailsResponse(**make_product_data())
        assert len(data.shipping_options) == 1
        assert isinstance(data.shipping_options[0], ShippingOption)
        assert data.shipping_options[0].shippingServiceCode == "UPS_GROUND"

    def test_empty_description_is_valid(self):
        """Empty string description is accepted."""
        data = ProductDetailsResponse(**make_product_data(description=""))
        assert data.description == ""

    def test_multiple_shipping_options(self):
        """Multiple shipping options are all valid."""
        data = ProductDetailsResponse(**make_product_data(
            shipping_options=[
                make_shipping_option(shippingServiceCode="UPS"),
                make_shipping_option(shippingServiceCode="FEDEX"),
            ]
        ))
        assert len(data.shipping_options) == 2

    def test_multiple_localized_aspects(self):
        """Multiple localized aspects are all valid."""
        data = ProductDetailsResponse(**make_product_data(
            localized_aspects=[
                make_localized_aspect(name="Color", value="Black"),
                make_localized_aspect(name="Size", value="Medium"),
            ]
        ))
        assert len(data.localized_aspects) == 2


# ==============================================================================
# Required Fields Tests
# ==============================================================================

class TestProductDetailsResponseRequiredFields:

    def test_missing_id_raises_error(self):
        """Missing id raises ValidationError."""
        product_data = make_product_data()
        del product_data["id"]
        with pytest.raises(ValidationError):
            ProductDetailsResponse(**product_data)

    def test_missing_title_raises_error(self):
        """Missing title raises ValidationError."""
        product_data = make_product_data()
        del product_data["title"]
        with pytest.raises(ValidationError):
            ProductDetailsResponse(**product_data)

    def test_missing_description_raises_error(self):
        """Missing description raises ValidationError."""
        product_data = make_product_data()
        del product_data["description"]
        with pytest.raises(ValidationError):
            ProductDetailsResponse(**product_data)

    def test_missing_price_raises_error(self):
        """Missing price raises ValidationError."""
        product_data = make_product_data()
        del product_data["price"]
        with pytest.raises(ValidationError):
            ProductDetailsResponse(**product_data)

    def test_invalid_price_type_raises_error(self):
        """Non-dict price raises ValidationError."""
        with pytest.raises(ValidationError):
            ProductDetailsResponse(**make_product_data(price="free"))

    def test_empty_payload_raises_error(self):
        """Empty payload raises ValidationError for required fields."""
        with pytest.raises(ValidationError) as exc_info:
            ProductDetailsResponse.model_validate({})
        errors = exc_info.value.errors()
        missing = {e["loc"][0] for e in errors if e["type"] == "missing"}
        assert "id" in missing
        assert "title" in missing
        assert "description" in missing
        assert "price" in missing


# ==============================================================================
# ORM Mapping Tests
# ==============================================================================

class TestProductDetailsResponseOrmMapping:

    def test_from_orm_object(self):
        """ProductDetailsResponse maps correctly from ORM-like object."""
        mock_product = MagicMock()
        mock_product.id = "v1|123456|0"
        mock_product.title = "Wireless Headphones"
        mock_product.description = "Great headphones."
        mock_product.price = Price(value=99.99, currency="USD")
        mock_product.image_url = "https://example.com/img.jpg"
        mock_product.additional_images = None
        mock_product.localized_aspects = []
        mock_product.shipping_options = []

        data = ProductDetailsResponse.model_validate(mock_product)
        assert data.id == "v1|123456|0"
        assert data.description == "Great headphones."
        assert isinstance(data.price, Price)

    def test_from_orm_with_none_optional_fields(self):
        """Maps correctly when optional fields are None."""
        mock_product = MagicMock()
        mock_product.id = "v1|123456|0"
        mock_product.title = "Wireless Headphones"
        mock_product.description = "Great headphones."
        mock_product.price = Price(value=99.99, currency="USD")
        mock_product.image_url = None
        mock_product.additional_images = None
        mock_product.localized_aspects = []
        mock_product.shipping_options = []

        data = ProductDetailsResponse.model_validate(mock_product)
        assert data.image_url is None
        assert data.additional_images is None


# ==============================================================================
# Comparison vs ProductSummaryResponse
# ==============================================================================

class TestProductDetailsVsSummary:

    def test_description_is_required_unlike_summary(self):
        """description is required in Details but absent in Summary."""
        product_data = make_product_data()
        del product_data["description"]
        with pytest.raises(ValidationError):
            ProductDetailsResponse(**product_data)

    def test_no_original_price_field(self):
        """ProductDetailsResponse has no original_price field."""
        data = ProductDetailsResponse(**make_product_data())
        assert not hasattr(data, "original_price")

    def test_price_is_object_not_float(self):
        """
        Key difference: ProductDetailsResponse.price is a Price object
        whereas ProductSummaryResponse.price is a plain float.
        """
        data = ProductDetailsResponse(**make_product_data())
        assert isinstance(data.price, Price)
        assert not isinstance(data.price, float)