from fastapi import FastAPI
from core.exception_handler import register_exceptions
from exceptions.auth_exceptions import EmailAlreadyExistsError
from models.base import Base
from routes import auth_route
from database import engine

app = FastAPI()

register_exceptions(app)

app.include_router(auth_route.router, prefix="/auth")

Base.metadata.create_all(engine)