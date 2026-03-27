from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.admin_auth import router as admin_auth_router
from app.api.routes.admin_categories import router as admin_categories_router
from app.api.routes.admin_logistics_companies import router as admin_logistics_companies_router
from app.api.routes.admin_orders import router as admin_orders_router
from app.api.routes.admin_products import router as admin_products_router
from app.api.routes.admin_uploads import router as admin_uploads_router
from app.api.routes.addresses import router as addresses_router
from app.api.routes.cart import router as cart_router
from app.api.routes.categories import router as categories_router
from app.api.routes.logistics_companies import router as logistics_companies_router
from app.api.routes.orders import router as orders_router
from app.api.routes.payments import router as payments_router
from app.api.routes.products import router as products_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(admin_auth_router)
api_router.include_router(admin_categories_router)
api_router.include_router(admin_logistics_companies_router)
api_router.include_router(admin_orders_router)
api_router.include_router(admin_products_router)
api_router.include_router(admin_uploads_router)
api_router.include_router(addresses_router)
api_router.include_router(cart_router)
api_router.include_router(categories_router)
api_router.include_router(logistics_companies_router)
api_router.include_router(orders_router)
api_router.include_router(payments_router)
api_router.include_router(products_router)
