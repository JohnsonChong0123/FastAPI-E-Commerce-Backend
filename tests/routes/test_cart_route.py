# tests/routes/test_cart_route.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from core.jwt import create_access_token
from core.security import hash_password
from models.user_model import User
from exceptions.product_exceptions import ProductNotFoundError
from main import app
from database import get_db


PATCH_PATH = "routes.cart_route.cart_services.add_to_cart"

VALID_PAYLOAD = {
    "product_id": "v1|123456|0",
    "quantity": 1
}


# ==============================================================================
# FIXTURES
# ==============================================================================
def auth_header(user_id) -> dict:
    """Helper — builds Authorization header with access token."""
    token = create_access_token(str(user_id))
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# Happy Path Tests
# ==============================================================================

class TestAddToCartRoute:

    @pytest.mark.asyncio
    async def test_add_to_cart_returns_200(self, client, registered_user):
        """Valid request returns 200."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_add:
            mock_add.return_value = {"message": "Added to cart successfully"}
            response = client.post(
                "/cart/add",
                json=VALID_PAYLOAD,
                headers=auth_header(registered_user.id)
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_to_cart_returns_success_message(
        self, client, registered_user
    ):
        """Valid request returns correct success message."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_add:
            mock_add.return_value = {"message": "Added to cart successfully"}
            response = client.post(
                "/cart/add",
                json=VALID_PAYLOAD,
                headers=auth_header(registered_user.id)
            )
            assert response.json() == {"message": "Added to cart successfully"}

    @pytest.mark.asyncio
    async def test_service_called_with_correct_payload(
        self, client, registered_user
    ):
        """Service is called with correct user and payload."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_add:
            mock_add.return_value = {"message": "Added to cart successfully"}
            client.post(
                "/cart/add",
                json=VALID_PAYLOAD,
                headers=auth_header(registered_user.id)
            )
            assert mock_add.called
            call_kwargs = mock_add.call_args
            payload_arg = call_kwargs[0][2]   # third positional arg
            assert payload_arg.product_id == "v1|123456|0"
            assert payload_arg.quantity == 1


# ==============================================================================
# Authentication Tests
# ==============================================================================

class TestAddToCartRouteAuth:

    def test_no_token_returns_401(self, client):
        """Missing Authorization header returns 401."""
        response = client.post("/cart/add", json=VALID_PAYLOAD)
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """Invalid token returns 401."""
        response = client.post(
            "/cart/add",
            json=VALID_PAYLOAD,
            headers={"Authorization": "Bearer invalid.token"}
        )
        assert response.status_code == 401

    def test_expired_token_returns_401(self, client):
        """Expired token returns 401."""
        from core.jwt import create_token
        expired = create_token("some-id", "access", expires_delta=-1)
        response = client.post(
            "/cart/add",
            json=VALID_PAYLOAD,
            headers={"Authorization": f"Bearer {expired}"}
        )
        assert response.status_code == 401


# ==============================================================================
# Validation Tests
# ==============================================================================

class TestAddToCartRouteValidation:

    def test_missing_product_id_returns_422(self, client, registered_user):
        """Missing product_id returns 422."""
        response = client.post(
            "/cart/add",
            json={"quantity": 1},
            headers=auth_header(registered_user.id)
        )
        assert response.status_code == 422

    def test_empty_product_id_returns_422(self, client, registered_user):
        """Empty product_id returns 422."""
        response = client.post(
            "/cart/add",
            json={"product_id": "", "quantity": 1},
            headers=auth_header(registered_user.id)
        )
        assert response.status_code == 422

    def test_missing_quantity_returns_422(self, client, registered_user):
        """Missing quantity returns 422."""
        response = client.post(
            "/cart/add",
            json={"product_id": "v1|123456|0"},
            headers=auth_header(registered_user.id)
        )
        assert response.status_code == 422

    def test_zero_quantity_returns_422(self, client, registered_user):
        """Zero quantity returns 422."""
        response = client.post(
            "/cart/add",
            json={"product_id": "v1|123456|0", "quantity": 0},
            headers=auth_header(registered_user.id)
        )
        assert response.status_code == 422

    def test_negative_quantity_returns_422(self, client, registered_user):
        """Negative quantity returns 422."""
        response = client.post(
            "/cart/add",
            json={"product_id": "v1|123456|0", "quantity": -1},
            headers=auth_header(registered_user.id)
        )
        assert response.status_code == 422


# ==============================================================================
# Error Path Tests
# ==============================================================================

class TestAddToCartRouteErrors:
    @pytest.mark.asyncio
    async def test_unexpected_error_returns_500(
        self, client, registered_user
    ):
        """Unexpected service error returns 500."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_add:
            mock_add.side_effect = Exception("Unexpected error")
            response = client.post(
                "/cart/add",
                json=VALID_PAYLOAD,
                headers=auth_header(registered_user.id)
            )
            assert response.status_code == 500


# ==============================================================================
# Transaction Tests
# ==============================================================================
class TestAddToCartRouteTransaction:
    @pytest.mark.asyncio
    async def test_db_commit_called_on_success(self, client, registered_user):
        mock_db = MagicMock() 
        
        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        try:
            with patch("routes.cart_route.cart_services.add_to_cart", new_callable=AsyncMock) as mock_service:
                mock_service.return_value = {"message": "Added to cart successfully"}
                
                client.post(
                    "/cart/add",
                    json=VALID_PAYLOAD,
                    headers=auth_header(registered_user.id)
                )

                mock_db.commit.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_db_rollback_called_on_failure(self, client, registered_user):
        mock_db = MagicMock()
        
        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        try:
            with patch("routes.cart_route.cart_services.add_to_cart", new_callable=AsyncMock) as mock_service:
                mock_service.side_effect = Exception("Service failed")
                
                client.post(
                    "/cart/add",
                    json=VALID_PAYLOAD,
                    headers=auth_header(registered_user.id)
                )

                mock_db.rollback.assert_called_once()
        finally:
            app.dependency_overrides.clear()