# tests/exceptions/test_auth_exceptions.py
import pytest

from exceptions.auth_exceptions import EmailAlreadyExistsError

class TestEmailAlreadyExistsError:

    def test_is_exception(self):
        """EmailAlreadyExistsError is a valid Python exception."""
        assert issubclass(EmailAlreadyExistsError, Exception)

    def test_can_be_raised(self):
        """EmailAlreadyExistsError can be raised and caught."""
        with pytest.raises(EmailAlreadyExistsError):
            raise EmailAlreadyExistsError()

    def test_can_be_caught_as_base_exception(self):
        """EmailAlreadyExistsError can be caught as a base Exception."""
        with pytest.raises(Exception):
            raise EmailAlreadyExistsError()