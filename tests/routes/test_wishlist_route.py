# tests/routes/test_wishlist_route.py
import uuid

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from core.jwt import create_access_token, create_refresh_token
from core.security import hash_password
from models.user_model import User
from exceptions.product_exceptions import ProductNotFoundError
from exceptions.wishlist_exceptions import WishlistNotFoundError


ADD_PATCH = "routes.wishlist_route.wishlist_services.add_to_wishlist"
GET_PATCH = "routes.wishlist_route.wishlist_services.get_wishlist"
REMOVE_PATCH = "routes.wishlist_route.wishlist_services.remove_wishlist"
CLEAR_PATCH = "routes.wishlist_route.wishlist_services.clear_wishlist"

MOCK_WISHLIST_ITEMS = [
    {
        "id": str(uuid.uuid4()),    
        "product_id": "v1|111|0",
        "name": "Wireless Headphones",
        "price": 99.99,
        "image_url": "https://example.com/img.jpg"
    }
]


# ==============================================================================
# FIXTURES
# ==============================================================================
def auth_header(user_id) -> dict:
    token = create_access_token(str(user_id))
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# POST /wishlist/add Tests
# ==============================================================================

class TestAddWishlistRoute:

    @pytest.mark.asyncio
    async def test_add_returns_200(self, client, registered_user):
        """Valid request returns 200."""
        with patch(ADD_PATCH, new_callable=AsyncMock) as mock_add:
            mock_add.return_value = {
                "message": "Added to wishlist successfully"
            }
            response = client.post(
                "/wishlist/add",
                json={"product_id": "v1|123456|0"},
                headers=auth_header(registered_user.id)
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_returns_success_message(self, client, registered_user):
        """Returns correct success message."""
        with patch(ADD_PATCH, new_callable=AsyncMock) as mock_add:
            mock_add.return_value = {
                "message": "Added to wishlist successfully"
            }
            response = client.post(
                "/wishlist/add",
                json={"product_id": "v1|123456|0"},
                headers=auth_header(registered_user.id)
            )
            assert response.json() == {
                "message": "Added to wishlist successfully"
            }

    @pytest.mark.asyncio
    async def test_add_product_not_found_returns_500(
        self, client, registered_user
    ):
        """
        ProductNotFoundError currently returns 500.
        Documents the bug — should return 404.
        Fix: catch ProductNotFoundError before generic except.
        """
        with patch(ADD_PATCH, new_callable=AsyncMock) as mock_add:
            mock_add.side_effect = ProductNotFoundError()
            response = client.post(
                "/wishlist/add",
                json={"product_id": "v1|123456|0"},
                headers=auth_header(registered_user.id)
            )
            assert response.status_code == 500   # ← documents bug

    @pytest.mark.asyncio
    async def test_add_exposes_error_details_bug(
        self, client, registered_user
    ):
        """
        DOCUMENTS SECURITY BUG: str(e) exposes internal error details.
        Error detail should be sanitized — not raw exception message.
        """
        with patch(ADD_PATCH, new_callable=AsyncMock) as mock_add:
            mock_add.side_effect = Exception("DB connection string: secret")
            response = client.post(
                "/wishlist/add",
                json={"product_id": "v1|123456|0"},
                headers=auth_header(registered_user.id)
            )
            # Exposes raw error — documents security gap
            assert "DB connection string" in response.json()["detail"]

    def test_add_no_token_returns_401(self, client):
        """Missing token returns 401."""
        response = client.post(
            "/wishlist/add",
            json={"product_id": "v1|123456|0"}
        )
        assert response.status_code == 401

    def test_add_missing_product_id_returns_422(self, client, registered_user):
        """Missing product_id returns 422."""
        response = client.post(
            "/wishlist/add",
            json={},
            headers=auth_header(registered_user.id)
        )
        assert response.status_code == 422

    def test_add_empty_product_id_returns_422(self, client, registered_user):
        """Empty product_id returns 422."""
        response = client.post(
            "/wishlist/add",
            json={"product_id": ""},
            headers=auth_header(registered_user.id)
        )
        assert response.status_code == 422


# ==============================================================================
# GET /wishlist Tests
# ==============================================================================

class TestGetWishlistRoute:

    @pytest.mark.asyncio
    async def test_get_returns_200(self, client, registered_user):
        """Valid request returns 200."""
        with patch(GET_PATCH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_WISHLIST_ITEMS
            response = client.get(
                "/wishlist",
                headers=auth_header(registered_user.id)
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_returns_list(self, client, registered_user):
        """Response is a list."""
        with patch(GET_PATCH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_WISHLIST_ITEMS
            response = client.get(
                "/wishlist",
                headers=auth_header(registered_user.id)
            )
            assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_returns_correct_item_fields(
        self, client, registered_user
    ):
        """Response items contain correct fields."""
        with patch(GET_PATCH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_WISHLIST_ITEMS
            response = client.get(
                "/wishlist",
                headers=auth_header(registered_user.id)
            )
            item = response.json()[0]
            assert "product_id" in item
            assert "name" in item
            assert "price" in item
            assert "image_url" in item

    @pytest.mark.asyncio
    async def test_get_empty_wishlist_returns_200(
        self, client, registered_user
    ):
        """Empty wishlist returns 200 with empty list."""
        with patch(GET_PATCH, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            response = client.get(
                "/wishlist",
                headers=auth_header(registered_user.id)
            )
            assert response.status_code == 200
            assert response.json() == []

    def test_get_no_token_returns_401(self, client):
        """Missing token returns 401."""
        response = client.get("/wishlist")
        assert response.status_code == 401

    def test_get_invalid_token_returns_401(self, client):
        """Invalid token returns 401."""
        response = client.get(
            "/wishlist",
            headers={"Authorization": "Bearer invalid.token"}
        )
        assert response.status_code == 401


# ==============================================================================
# DELETE /wishlist/remove/{product_id} Tests
# ==============================================================================

class TestRemoveWishlistRoute:

    def test_remove_returns_200(self, client, registered_user):
        """Valid request returns 200."""
        with patch(REMOVE_PATCH) as mock_remove:
            mock_remove.return_value = {
                "message": "Wishlist removed successfully"
            }
            response = client.delete(
                "/wishlist/remove/v1|123456|0",
                headers=auth_header(registered_user.id)
            )
            assert response.status_code == 200

    def test_remove_returns_success_message(self, client, registered_user):
        """Returns correct success message."""
        with patch(REMOVE_PATCH) as mock_remove:
            mock_remove.return_value = {
                "message": "Wishlist removed successfully"
            }
            response = client.delete(
                "/wishlist/remove/v1|123456|0",
                headers=auth_header(registered_user.id)
            )
            assert response.json() == {
                "message": "Wishlist removed successfully"
            }

    def test_remove_item_not_found_returns_500(self, client, registered_user):
        """
        WishlistNotFoundError currently returns 500.
        Documents the bug — should return 404.
        """
        with patch(REMOVE_PATCH) as mock_remove:
            mock_remove.side_effect = WishlistNotFoundError()
            response = client.delete(
                "/wishlist/remove/v1|nonexistent|0",
                headers=auth_header(registered_user.id)
            )
            assert response.status_code == 500   # ← documents bug

    def test_remove_no_token_returns_401(self, client):
        """Missing token returns 401."""
        response = client.delete("/wishlist/remove/v1|123456|0")
        assert response.status_code == 401


# ==============================================================================
# DELETE /wishlist/clear Tests
# ==============================================================================

class TestClearWishlistRoute:

    def test_clear_returns_200(self, client, registered_user):
        """Valid request returns 200."""
        with patch(CLEAR_PATCH) as mock_clear:
            mock_clear.return_value = {
                "message": "Wishlist cleared successfully"
            }
            response = client.delete(
                "/wishlist/clear",
                headers=auth_header(registered_user.id)
            )
            assert response.status_code == 200

    def test_clear_returns_success_message(self, client, registered_user):
        """Returns correct success message."""
        with patch(CLEAR_PATCH) as mock_clear:
            mock_clear.return_value = {
                "message": "Wishlist cleared successfully"
            }
            response = client.delete(
                "/wishlist/clear",
                headers=auth_header(registered_user.id)
            )
            assert response.json() == {
                "message": "Wishlist cleared successfully"
            }

    def test_clear_no_wishlist_returns_500(self, client, registered_user):
        """
        WishlistNotFoundError currently returns 500.
        Documents the bug — should return 404.
        """
        with patch(CLEAR_PATCH) as mock_clear:
            mock_clear.side_effect = WishlistNotFoundError()
            response = client.delete(
                "/wishlist/clear",
                headers=auth_header(registered_user.id)
            )
            assert response.status_code == 500   # ← documents bug

    def test_clear_no_token_returns_401(self, client):
        """Missing token returns 401."""
        response = client.delete("/wishlist/clear")
        assert response.status_code == 401