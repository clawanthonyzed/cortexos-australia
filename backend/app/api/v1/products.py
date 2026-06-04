"""Product CRUD endpoints."""
from __future__ import annotations

import json
import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db, paginate
from app.models.product import Product, ProductStatus
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductRead,
    ProductReadBrief,
    ProductUpdate,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


def _error(msg: str, detail: Any = None) -> dict[str, Any]:
    return {"error": msg, "detail": detail or {}}


@router.get("", response_model=dict[str, Any], tags=["products"])
async def list_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCT_READ)),
    pagination: dict = Depends(paginate),
    status_filter: str | None = Query(None, alias="status"),
    category: str | None = Query(None),
    is_featured: bool | None = Query(None),
) -> dict[str, Any]:
    """List all products with pagination and filtering."""
    stmt = select(Product)
    if status_filter:
        stmt = stmt.where(Product.status == status_filter)
    if category:
        stmt = stmt.where(Product.category == category)
    if is_featured is not None:
        stmt = stmt.where(Product.is_featured == is_featured)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset(pagination["offset"]).limit(pagination["limit"]).order_by(
        Product.is_featured.desc(), Product.created_at.desc()
    )
    result = await db.execute(stmt)
    products = result.scalars().all()

    return {
        "items": [ProductReadBrief.model_validate(p) for p in products],
        "total": total,
        "page": pagination["page"],
        "page_size": pagination["page_size"],
    }


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED, tags=["products"])
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCT_CREATE)),
) -> ProductRead:
    """Create a new product."""
    existing = await db.execute(select(Product).where(Product.slug == payload.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_error("Product slug already in use"),
        )

    product = Product(
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        short_description=payload.short_description,
        product_type=payload.product_type,
        category=payload.category,
        tags=json.dumps(payload.tags),
        price_aud=payload.price_aud,
        original_price_aud=payload.original_price_aud,
        is_free=payload.is_free,
        cover_image_url=payload.cover_image_url,
        seo_title=payload.seo_title,
        seo_description=payload.seo_description,
        seo_keywords=json.dumps(payload.seo_keywords),
        listings_json=json.dumps(
            {k: v.model_dump() for k, v in payload.listings.items()}
        ),
        assets_json=json.dumps([a.model_dump() for a in payload.assets]),
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return _product_to_schema(product)


@router.get("/{product_id}", response_model=ProductRead, tags=["products"])
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCT_READ)),
) -> ProductRead:
    """Get a product by ID."""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail=_error("Product not found"))
    product.view_count += 1
    await db.flush()
    return _product_to_schema(product)


@router.get("/slug/{slug}", response_model=ProductRead, tags=["products"])
async def get_product_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCT_READ)),
) -> ProductRead:
    """Get a product by slug."""
    result = await db.execute(select(Product).where(Product.slug == slug))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=_error("Product not found"))
    return _product_to_schema(product)


@router.patch("/{product_id}", response_model=ProductRead, tags=["products"])
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCT_UPDATE)),
) -> ProductRead:
    """Update a product."""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail=_error("Product not found"))

    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        if field in ("tags", "seo_keywords"):
            setattr(product, field, json.dumps(value))
        else:
            setattr(product, field, value)

    await db.flush()
    await db.refresh(product)
    return _product_to_schema(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, tags=["products"])
async def delete_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCT_DELETE)),
) -> None:
    """Delete a product."""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail=_error("Product not found"))
    await db.delete(product)


@router.post("/{product_id}/publish", response_model=ProductRead, tags=["products"])
async def publish_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PRODUCT_UPDATE)),
) -> ProductRead:
    """Publish a draft product."""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail=_error("Product not found"))
    product.status = ProductStatus.PUBLISHED
    await db.flush()
    await db.refresh(product)
    return _product_to_schema(product)


def _product_to_schema(product: Product) -> ProductRead:
    """Convert a Product ORM object to ProductRead, parsing JSON fields."""
    try:
        tags = json.loads(product.tags)
    except (json.JSONDecodeError, TypeError):
        tags = []
    try:
        seo_keywords = json.loads(product.seo_keywords)
    except (json.JSONDecodeError, TypeError):
        seo_keywords = []
    try:
        listings = json.loads(product.listings_json)
    except (json.JSONDecodeError, TypeError):
        listings = {}
    try:
        assets = json.loads(product.assets_json)
    except (json.JSONDecodeError, TypeError):
        assets = []

    return ProductRead(
        id=product.id,
        name=product.name,
        slug=product.slug,
        description=product.description,
        short_description=product.short_description,
        product_type=product.product_type,
        category=product.category,
        tags=tags,
        price_aud=product.price_aud,
        original_price_aud=product.original_price_aud,
        is_free=product.is_free,
        cover_image_url=product.cover_image_url,
        seo_title=product.seo_title,
        seo_description=product.seo_description,
        seo_keywords=seo_keywords,
        status=product.status,
        is_featured=product.is_featured,
        listings=listings,
        assets=assets,
        total_sales=product.total_sales,
        total_revenue_aud=product.total_revenue_aud,
        view_count=product.view_count,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )
