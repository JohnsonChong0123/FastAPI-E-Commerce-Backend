# core/exception_handler.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from exceptions.auth_exceptions import EmailAlreadyExistsError

async def email_exists_handler(request: Request, exc: EmailAlreadyExistsError):
    """Handle the EmailAlreadyExistsError by returning a JSON response with a 409 status code."""
    return JSONResponse(
        status_code=409,
        content={"detail": "Email already registered"}
    )

def register_exceptions(app: FastAPI):
    """Register all custom exception handlers with the FastAPI app."""
    app.add_exception_handler(EmailAlreadyExistsError, email_exists_handler)
    