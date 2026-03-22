from fastapi import APIRouter
from schemas.product.product_sum_response import ProductSummaryResponse
from services.product import product_services

router = APIRouter()

@router.get("/list-products", response_model=list[ProductSummaryResponse])
async def list_products():
    return await product_services.get_products()