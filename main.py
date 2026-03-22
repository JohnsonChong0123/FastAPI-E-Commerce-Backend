from fastapi import FastAPI
from core.exception_handler import register_exceptions
from models.base import Base
from routes import auth_route, product_route, user_route
from database import engine

app = FastAPI()

register_exceptions(app)

app.include_router(auth_route.router, prefix="/auth")
app.include_router(product_route.router, prefix="/product")
app.include_router(user_route.router, prefix="/user")

Base.metadata.create_all(engine)