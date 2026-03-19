# tests/schemas/auth/test_register_request.py
import pytest
from pydantic import ValidationError
from schemas.auth.register_request import RegisterRequest

# ==============================================================================
# SHARED FIXTURE
# ==============================================================================

@pytest.fixture
def valid_payload() -> dict:
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "password": "Secret1234!",
    }

# ==============================================================================
# VALID DATA TESTS
# ==============================================================================

class TestRegisterRequestValidData:

    def test_valid_full_registration(self, valid_payload):
        """All required fields plus optional phone."""
        data = RegisterRequest(**valid_payload, phone="0123456789")
        assert data.first_name == "John"
        assert data.last_name == "Doe"
        assert data.email == "john@example.com"
        assert data.phone == "0123456789"

    def test_valid_registration_without_phone(self, valid_payload):
        """Phone is optional and defaults to None."""
        data = RegisterRequest(**valid_payload)
        assert data.phone is None


# ==============================================================================
# EMAIL VALIDATION TESTS
# ==============================================================================

class TestRegisterRequestEmailValidation:

    def test_email_is_normalized_to_lowercase(self, valid_payload):
        """Email should be case-insensitive and stored in lowercase."""
        # data = RegisterRequest(**{**valid_payload, "email": "JOHN@EXAMPLE.COM"})
        payload = {**valid_payload, "email": "JOHN@EXAMPLE.COM"}
        data = RegisterRequest(**payload)
        assert data.email == "john@example.com"

    @pytest.mark.parametrize("bad_email", [
        "not-an-email",
        "john@",
        "johnexample.com",
        "",
    ])
    def test_invalid_email_raises_error(self, valid_payload, bad_email):
        """Invalid email formats should raise a validation error."""
        with pytest.raises(ValidationError):
            RegisterRequest(**{**valid_payload, "email": bad_email})

    def test_missing_email_raises_error(self, valid_payload):
        """Email is required, so omitting it should raise a validation error."""
        valid_payload.pop("email")
        with pytest.raises(ValidationError):
            RegisterRequest(**valid_payload)


# ==============================================================================
# PASSWORD VALIDATION TESTS
# ==============================================================================

class TestRegisterRequestPasswordValidation:

    def test_valid_strong_password(self, valid_payload):
        """A password that meets all criteria should be accepted."""
        data = RegisterRequest(**valid_payload)
        assert data.password == "Secret1234!"

    def test_password_too_short_raises_error(self, valid_payload):
        """Passwords must be at least 8 characters long."""
        with pytest.raises(ValidationError, match="8"):
            RegisterRequest(**{**valid_payload, "password": "Ab1!"})

    def test_password_missing_uppercase_raises_error(self, valid_payload):
        """Passwords must contain at least one uppercase letter."""
        with pytest.raises(ValidationError, match="(?i)uppercase"):
            RegisterRequest(**{**valid_payload, "password": "secret1234!"})

    def test_password_missing_digit_raises_error(self, valid_payload):
        """Passwords must contain at least one digit."""
        with pytest.raises(ValidationError, match="(?i)number"):
            RegisterRequest(**{**valid_payload, "password": "SecretPass!"})
            
    def test_password_missing_symbol_raises_error(self, valid_payload):
        """Passwords must contain at least one special character."""
        with pytest.raises(ValidationError, match="(?i)special"):
            RegisterRequest(**{**valid_payload, "password": "SecretPass1"})

    @pytest.mark.parametrize("bad_password", ["", None])
    def test_empty_or_missing_password_raises_error(self, valid_payload, bad_password):
        """Empty or None passwords should raise a validation error."""
        with pytest.raises(ValidationError):
            RegisterRequest(**{**valid_payload, "password": bad_password})

    def test_missing_password_raises_error(self, valid_payload):
        """Password is required, so omitting it should raise a validation error."""
        valid_payload.pop("password")
        with pytest.raises(ValidationError):
            RegisterRequest(**valid_payload)


# ==============================================================================
# NAME VALIDATION TESTS
# ==============================================================================

class TestRegisterRequestNameValidation:

    def test_valid_name_with_spaces_stripped(self, valid_payload):
        """Leading and trailing spaces in names should be stripped."""
        data = RegisterRequest(**{**valid_payload, "first_name": "  John  ", "last_name": "  Doe  "})
        assert data.first_name == "John"
        assert data.last_name == "Doe"

    @pytest.mark.parametrize("field,value", [
        ("first_name", ""),
        ("first_name", "   "),
        ("last_name", ""),
        ("last_name", "   "),
    ])
    def test_blank_name_raises_error(self, valid_payload, field, value):
        """Names cannot be blank or just whitespace."""
        with pytest.raises(ValidationError):
            RegisterRequest(**{**valid_payload, field: value})

    @pytest.mark.parametrize("field", ["first_name", "last_name"])
    def test_missing_name_raises_error(self, valid_payload, field):
        """Both first_name and last_name are required, so omitting either should raise a validation error."""
        valid_payload.pop(field)
        with pytest.raises(ValidationError):
            RegisterRequest(**valid_payload)


# ==============================================================================
# MISSING REQUIRED FIELDS TESTS
# ==============================================================================

class TestRegisterRequestMissingFields:

    def test_empty_payload_raises_error_for_all_required_fields(self):
        """An empty payload should raise a validation error indicating all required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest()
        missing = {
            e["loc"][0] for e in exc_info.value.errors() if e["type"] == "missing"
        }
        assert missing == {"first_name", "last_name", "email", "password"}

    def test_empty_payload_has_exactly_four_missing_fields(self):
        """An empty payload should raise a validation error with exactly four missing field errors."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest()
        missing_count = sum(1 for e in exc_info.value.errors() if e["type"] == "missing")
        assert missing_count == 4