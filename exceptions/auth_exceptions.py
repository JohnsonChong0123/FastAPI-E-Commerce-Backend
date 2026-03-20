# exceptions/auth_exceptions.py
class EmailAlreadyExistsError(Exception):
    pass

class InvalidCredentialsError(Exception):
    pass

class TokenExpiredError(Exception):
    pass

class InvalidTokenError(Exception):
    pass

class InvalidGoogleTokenError(Exception):
    pass

class AuthProviderMismatchError(Exception):
    pass