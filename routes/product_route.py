from fastapi import APIRouter
from schemas.product.product_details_response import ProductDetailsResponse
from schemas.product.product_sum_response import ProductSummaryResponse
from services.product import product_services

router = APIRouter()

@router.get("/list-products", response_model=list[ProductSummaryResponse])
async def list_products():
    return await product_services.get_products()

@router.get("/{product_id}", response_model=ProductDetailsResponse)
async def get_product_details(product_id: str):
    return await product_services.get_product_details(product_id)