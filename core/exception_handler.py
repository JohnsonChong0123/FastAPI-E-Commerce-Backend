# core/exception_handler.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from exceptions.auth_exceptions import EmailAlreadyExistsError, InvalidCredentialsError, InvalidTokenError, TokenExpiredError

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

def register_exceptions(app: FastAPI):
    """Register all custom exception handlers with the FastAPI app."""
    app.add_exception_handler(EmailAlreadyExistsError, email_exists_handler)
    app.add_exception_handler(InvalidCredentialsError, invalid_credentials_handler)
    app.add_exception_handler(TokenExpiredError, token_expired_handler)
    app.add_exception_handler(InvalidTokenError, invalid_token_handler)
