# core/exception_handler.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from exceptions.auth_exceptions import AuthProviderMismatchError, EmailAlreadyExistsError, InvalidCredentialsError, InvalidFacebookTokenError, InvalidGoogleTokenError, InvalidTokenError, TokenExpiredError
from exceptions.product_exceptions import EbayAuthError, ExternalAPIError

async def email_exists_handler(request: Request, exc: EmailAlreadyExistsError):
    """Handle the EmailAlreadyExistsError by returning a JSON response with a 409 status code."""
    return JSONResponse(
        status_code=409,
        content={"detail": "Email already registered"}
    )
    
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid email or password"}
    )
    
async def token_expired_handler(request: Request, exc: TokenExpiredError):
        return JSONResponse(
            status_code=401,
            content={"detail": "Token expired"}
        )

async def invalid_token_handler(request: Request, exc: InvalidTokenError):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid token"}
    )
    
async def invalid_google_token_handler(request: Request, exc: InvalidGoogleTokenError):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid Google token"}
    )
    
async def provider_mismatch_handler(request: Request, exc: AuthProviderMismatchError):
    return JSONResponse(
        status_code=409,
        content={"detail": "Account exists with different login method"}
    )
    
async def fb_token_handler(request: Request, exc: InvalidFacebookTokenError):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid Facebook token"}
    )
    
async def external_api_handler(request: Request, exc: ExternalAPIError):
    return JSONResponse(
        status_code=502,
        content={"detail": "Failed to fetch external products"}
    )
    
async def ebay_auth_handler(request: Request, exc: EbayAuthError):
    return JSONResponse(
        status_code=500,
        content={"detail": "eBay authentication failed"}
    )

def register_exceptions(app: FastAPI):
    """Register all custom exception handlers with the FastAPI app."""
    app.add_exception_handler(EmailAlreadyExistsError, email_exists_handler)
    app.add_exception_handler(InvalidCredentialsError, invalid_credentials_handler)
    app.add_exception_handler(TokenExpiredError, token_expired_handler)
    app.add_exception_handler(InvalidTokenError, invalid_token_handler)
    app.add_exception_handler(InvalidGoogleTokenError, invalid_google_token_handler)
    app.add_exception_handler(AuthProviderMismatchError, provider_mismatch_handler)
    app.add_exception_handler(InvalidFacebookTokenError, fb_token_handler)
    app.add_exception_handler(ExternalAPIError, external_api_handler)
    app.add_exception_handler(EbayAuthError, ebay_auth_handler)