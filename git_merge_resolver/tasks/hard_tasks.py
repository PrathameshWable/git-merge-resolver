"""
Hard difficulty task scenarios for the Git Merge Conflict Resolver.

Task 5: Multi-file conflicts requiring architectural pattern recognition
and cross-file consistency. Simulates a real API overhaul scenario.
"""

from __future__ import annotations

from git_merge_resolver.models import ConflictBlock


# ---------------------------------------------------------------------------
# Task 5: multi_file_api_overhaul
# Scenario: Developer A overhauled the REST API from v1 to v2:
#   - Changed paths from /api/v1/ to /api/v2/
#   - Replaced dict returns with Pydantic response models
#   - Standardized error handling with HTTPException
# Developer B added new /products/ endpoints and tests using old v1 patterns.
# Conflicts span: api/routes.py, api/schemas.py, tests/test_api.py
# ---------------------------------------------------------------------------

_TASK5_ROUTES_FILE = """\
\"\"\"
FastAPI route definitions for the product catalog API.

v2 routes use Pydantic response models for type-safe serialization
and HTTPException for standardized error responses.
\"\"\"

from __future__ import annotations

from typing import List, Optional
<<<<<<< main
from fastapi import APIRouter, HTTPException, Query, status
from api.schemas import (
    CategoryResponse,
    CategoryListResponse,
    ProductResponse,
    ProductListResponse,
    ProductCreateRequest,
    ErrorResponse,
)
from api.database import get_db_session
=======
from fastapi import APIRouter, Query
from api.database import get_db_session
>>>>>>> feature/product-catalog-v2

router = APIRouter()

<<<<<<< main
@router.get("/api/v2/categories", response_model=CategoryListResponse, tags=["categories"])
async def list_categories(
    active_only: bool = Query(default=True, description="Filter to active categories only"),
) -> CategoryListResponse:
    \"\"\"Return all product categories.\"\"\"
    async with get_db_session() as db:
        rows = await db.fetch_all(
            "SELECT id, name, slug, active FROM categories WHERE active = :active",
            {"active": active_only},
        )
        categories = [
            CategoryResponse(id=r["id"], name=r["name"], slug=r["slug"], active=r["active"])
            for r in rows
        ]
        return CategoryListResponse(categories=categories, total=len(categories))


@router.get(
    "/api/v2/categories/{category_id}",
    response_model=CategoryResponse,
    tags=["categories"],
)
async def get_category(category_id: int) -> CategoryResponse:
    \"\"\"Return a single category by ID.\"\"\"
    async with get_db_session() as db:
        row = await db.fetch_one(
            "SELECT id, name, slug, active FROM categories WHERE id = :id",
            {"id": category_id},
        )
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category {category_id} not found",
            )
        return CategoryResponse(
            id=row["id"], name=row["name"], slug=row["slug"], active=row["active"]
        )
=======
@router.get("/api/v1/categories")
async def list_categories(active_only: bool = Query(default=True)):
    \"\"\"Return all product categories.\"\"\"
    async with get_db_session() as db:
        rows = await db.fetch_all(
            "SELECT id, name, slug, active FROM categories WHERE active = :active",
            {"active": active_only},
        )
        return {"categories": [dict(r) for r in rows], "total": len(rows)}


@router.get("/api/v1/categories/{category_id}")
async def get_category(category_id: int):
    \"\"\"Return a single category by ID.\"\"\"
    async with get_db_session() as db:
        row = await db.fetch_one(
            "SELECT id, name, slug, active FROM categories WHERE id = :id",
            {"id": category_id},
        )
        if row is None:
            return {"error": f"Category {category_id} not found"}, 404
        return dict(row)


@router.get("/api/v1/products")
async def list_products(
    category_id: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    \"\"\"Return a paginated list of products, optionally filtered by category.\"\"\"
    async with get_db_session() as db:
        query = "SELECT id, name, sku, price, category_id, in_stock FROM products"
        params: dict = {}
        if category_id is not None:
            query += " WHERE category_id = :category_id"
            params["category_id"] = category_id
        query += f" LIMIT {page_size} OFFSET {(page - 1) * page_size}"
        rows = await db.fetch_all(query, params)
        return {"products": [dict(r) for r in rows], "page": page, "page_size": page_size}


@router.post("/api/v1/products", status_code=201)
async def create_product(payload: dict):
    \"\"\"Create a new product in the catalog.\"\"\"
    async with get_db_session() as db:
        result = await db.execute(
            "INSERT INTO products (name, sku, price, category_id, in_stock) "
            "VALUES (:name, :sku, :price, :category_id, :in_stock)",
            payload,
        )
        return {"id": result, **payload}
>>>>>>> feature/product-catalog-v2


@router.get(
    "/api/v2/products",
    response_model=ProductListResponse,
    tags=["products"],
)
async def list_products(
    category_id: Optional[int] = Query(default=None, description="Filter by category"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ProductListResponse:
    \"\"\"Return a paginated list of products, optionally filtered by category.\"\"\"
    async with get_db_session() as db:
        query = "SELECT id, name, sku, price, category_id, in_stock FROM products"
        params: dict = {}
        if category_id is not None:
            query += " WHERE category_id = :category_id"
            params["category_id"] = category_id
        query += f" LIMIT {page_size} OFFSET {(page - 1) * page_size}"
        rows = await db.fetch_all(query, params)
        products = [
            ProductResponse(
                id=r["id"],
                name=r["name"],
                sku=r["sku"],
                price=r["price"],
                category_id=r["category_id"],
                in_stock=r["in_stock"],
            )
            for r in rows
        ]
        return ProductListResponse(products=products, page=page, page_size=page_size)


@router.post(
    "/api/v2/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["products"],
)
async def create_product(payload: ProductCreateRequest) -> ProductResponse:
    \"\"\"Create a new product in the catalog.\"\"\"
    async with get_db_session() as db:
        result = await db.execute(
            "INSERT INTO products (name, sku, price, category_id, in_stock) "
            "VALUES (:name, :sku, :price, :category_id, :in_stock)",
            payload.model_dump(),
        )
        return ProductResponse(id=result, **payload.model_dump())
"""

_TASK5_SCHEMAS_FILE = """\
\"\"\"
Pydantic schemas for the product catalog API v2.

All response models include explicit field definitions to ensure
type-safe serialization and clear API contracts.
\"\"\"

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

<<<<<<< main
class CategoryResponse(BaseModel):
    \"\"\"Response schema for a single product category.\"\"\"

    id: int
    name: str
    slug: str
    active: bool


class CategoryListResponse(BaseModel):
    \"\"\"Paginated list of categories.\"\"\"

    categories: List[CategoryResponse]
    total: int


class ProductResponse(BaseModel):
    \"\"\"Response schema for a single product.\"\"\"

    id: int
    name: str
    sku: str
    price: float = Field(..., ge=0, description="Unit price in USD")
    category_id: int
    in_stock: bool

    @field_validator("price")
    @classmethod
    def price_must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("price must be non-negative")
        return round(v, 2)


class ProductListResponse(BaseModel):
    \"\"\"Paginated list of products.\"\"\"

    products: List[ProductResponse]
    page: int
    page_size: int


class ProductCreateRequest(BaseModel):
    \"\"\"Request body for creating a new product.\"\"\"

    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=50, pattern=r"^[A-Z0-9\\-]+$")
    price: float = Field(..., ge=0)
    category_id: int
    in_stock: bool = True


class ErrorResponse(BaseModel):
    \"\"\"Standard error response body.\"\"\"

    detail: str
    status_code: int
=======
# v1 had no formal schemas — responses were raw dicts.
# Developer B added these new schemas for inventory tracking:

class InventoryEntry(BaseModel):
    \"\"\"Represents a warehouse inventory record for a product.\"\"\"

    product_id: int
    warehouse_id: str
    quantity: int = Field(..., ge=0)
    reserved: int = Field(default=0, ge=0)

    @property
    def available(self) -> int:
        \"\"\"Units available for sale (total minus reserved).\"\"\"
        return self.quantity - self.reserved


class InventoryUpdateRequest(BaseModel):
    \"\"\"Request body for updating inventory levels.\"\"\"

    warehouse_id: str
    quantity_delta: int
    reason: str = Field(..., min_length=1, max_length=500)
>>>>>>> feature/product-catalog-v2
"""

_TASK5_TESTS_FILE = """\
\"\"\"
Integration tests for the product catalog API.
\"\"\"

from __future__ import annotations

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


<<<<<<< main
class TestCategoriesV2:
    \"\"\"Tests for the /api/v2/categories endpoints.\"\"\"

    def test_list_categories_returns_200(self):
        response = client.get("/api/v2/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "total" in data
        assert isinstance(data["categories"], list)

    def test_get_category_not_found_returns_404(self):
        response = client.get("/api/v2/categories/99999")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_list_categories_active_filter(self):
        response = client.get("/api/v2/categories?active_only=false")
        assert response.status_code == 200
=======
class TestCategoriesV1:
    \"\"\"Tests for the /api/v1/categories endpoints.\"\"\"

    def test_list_categories_returns_200(self):
        response = client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)

    def test_get_category_not_found_returns_404(self):
        response = client.get("/api/v1/categories/99999")
        assert response.status_code == 404

    def test_list_categories_active_filter(self):
        response = client.get("/api/v1/categories?active_only=false")
        assert response.status_code == 200


class TestProductsV1:
    \"\"\"Tests for the v1 product endpoints added by Developer B.\"\"\"

    def test_list_products_returns_200(self):
        response = client.get("/api/v1/products")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "page" in data

    def test_list_products_filter_by_category(self):
        response = client.get("/api/v1/products?category_id=1")
        assert response.status_code == 200

    def test_create_product_returns_201(self):
        payload = {
            "name": "Widget Pro",
            "sku": "WGT-001",
            "price": 29.99,
            "category_id": 1,
            "in_stock": True,
        }
        response = client.post("/api/v1/products", json=payload)
        assert response.status_code == 201
        assert "id" in response.json()
>>>>>>> feature/product-catalog-v2


class TestProductsV2:
    \"\"\"Tests for the /api/v2/products endpoints.\"\"\"

    def test_list_products_returns_200(self):
        response = client.get("/api/v2/products")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "page" in data
        assert "page_size" in data

    def test_list_products_response_schema(self):
        response = client.get("/api/v2/products")
        data = response.json()
        if data["products"]:
            product = data["products"][0]
            assert all(
                key in product for key in ["id", "name", "sku", "price", "in_stock"]
            )

    def test_create_product_returns_201(self):
        payload = {
            "name": "Test Widget",
            "sku": "TST-001",
            "price": 9.99,
            "category_id": 1,
            "in_stock": True,
        }
        response = client.post("/api/v2/products", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["sku"] == payload["sku"]
"""

# Conflict data
TASK5_ROUTES_C001_OURS = """\
from fastapi import APIRouter, HTTPException, Query, status
from api.schemas import (
    CategoryResponse,
    CategoryListResponse,
    ProductResponse,
    ProductListResponse,
    ProductCreateRequest,
    ErrorResponse,
)
from api.database import get_db_session
"""
TASK5_ROUTES_C001_THEIRS = """\
from fastapi import APIRouter, Query
from api.database import get_db_session
"""
TASK5_ROUTES_C001_GT = """\
from fastapi import APIRouter, HTTPException, Query, status
from api.schemas import (
    CategoryResponse,
    CategoryListResponse,
    ProductResponse,
    ProductListResponse,
    ProductCreateRequest,
    ErrorResponse,
    InventoryEntry,
    InventoryUpdateRequest,
)
from api.database import get_db_session
"""

TASK5_ROUTES_C002_OURS = """\
@router.get("/api/v2/categories", response_model=CategoryListResponse, tags=["categories"])
async def list_categories(
    active_only: bool = Query(default=True, description="Filter to active categories only"),
) -> CategoryListResponse:
    \"\"\"Return all product categories.\"\"\"
    async with get_db_session() as db:
        rows = await db.fetch_all(
            "SELECT id, name, slug, active FROM categories WHERE active = :active",
            {"active": active_only},
        )
        categories = [
            CategoryResponse(id=r["id"], name=r["name"], slug=r["slug"], active=r["active"])
            for r in rows
        ]
        return CategoryListResponse(categories=categories, total=len(categories))


@router.get(
    "/api/v2/categories/{category_id}",
    response_model=CategoryResponse,
    tags=["categories"],
)
async def get_category(category_id: int) -> CategoryResponse:
    \"\"\"Return a single category by ID.\"\"\"
    async with get_db_session() as db:
        row = await db.fetch_one(
            "SELECT id, name, slug, active FROM categories WHERE id = :id",
            {"id": category_id},
        )
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category {category_id} not found",
            )
        return CategoryResponse(
            id=row["id"], name=row["name"], slug=row["slug"], active=row["active"]
        )
"""
TASK5_ROUTES_C002_THEIRS = """\
@router.get("/api/v1/categories")
async def list_categories(active_only: bool = Query(default=True)):
    \"\"\"Return all product categories.\"\"\"
    async with get_db_session() as db:
        rows = await db.fetch_all(
            "SELECT id, name, slug, active FROM categories WHERE active = :active",
            {"active": active_only},
        )
        return {"categories": [dict(r) for r in rows], "total": len(rows)}


@router.get("/api/v1/categories/{category_id}")
async def get_category(category_id: int):
    \"\"\"Return a single category by ID.\"\"\"
    async with get_db_session() as db:
        row = await db.fetch_one(
            "SELECT id, name, slug, active FROM categories WHERE id = :id",
            {"id": category_id},
        )
        if row is None:
            return {"error": f"Category {category_id} not found"}, 404
        return dict(row)


@router.get("/api/v1/products")
async def list_products(
    category_id: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    \"\"\"Return a paginated list of products, optionally filtered by category.\"\"\"
    async with get_db_session() as db:
        query = "SELECT id, name, sku, price, category_id, in_stock FROM products"
        params: dict = {}
        if category_id is not None:
            query += " WHERE category_id = :category_id"
            params["category_id"] = category_id
        query += f" LIMIT {page_size} OFFSET {(page - 1) * page_size}"
        rows = await db.fetch_all(query, params)
        return {"products": [dict(r) for r in rows], "page": page, "page_size": page_size}


@router.post("/api/v1/products", status_code=201)
async def create_product(payload: dict):
    \"\"\"Create a new product in the catalog.\"\"\"
    async with get_db_session() as db:
        result = await db.execute(
            "INSERT INTO products (name, sku, price, category_id, in_stock) "
            "VALUES (:name, :sku, :price, :category_id, :in_stock)",
            payload,
        )
        return {"id": result, **payload}
"""
TASK5_ROUTES_C002_GT = """\
@router.get("/api/v2/categories", response_model=CategoryListResponse, tags=["categories"])
async def list_categories(
    active_only: bool = Query(default=True, description="Filter to active categories only"),
) -> CategoryListResponse:
    \"\"\"Return all product categories.\"\"\"
    async with get_db_session() as db:
        rows = await db.fetch_all(
            "SELECT id, name, slug, active FROM categories WHERE active = :active",
            {"active": active_only},
        )
        categories = [
            CategoryResponse(id=r["id"], name=r["name"], slug=r["slug"], active=r["active"])
            for r in rows
        ]
        return CategoryListResponse(categories=categories, total=len(categories))


@router.get(
    "/api/v2/categories/{category_id}",
    response_model=CategoryResponse,
    tags=["categories"],
)
async def get_category(category_id: int) -> CategoryResponse:
    \"\"\"Return a single category by ID.\"\"\"
    async with get_db_session() as db:
        row = await db.fetch_one(
            "SELECT id, name, slug, active FROM categories WHERE id = :id",
            {"id": category_id},
        )
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category {category_id} not found",
            )
        return CategoryResponse(
            id=row["id"], name=row["name"], slug=row["slug"], active=row["active"]
        )


@router.get(
    "/api/v2/products/inventory/{product_id}",
    response_model=InventoryEntry,
    tags=["inventory"],
)
async def get_product_inventory(product_id: int) -> InventoryEntry:
    \"\"\"Return inventory details for a product.\"\"\"
    async with get_db_session() as db:
        row = await db.fetch_one(
            "SELECT product_id, warehouse_id, quantity, reserved FROM inventory "
            "WHERE product_id = :product_id",
            {"product_id": product_id},
        )
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory for product {product_id} not found",
            )
        return InventoryEntry(**dict(row))


@router.patch(
    "/api/v2/products/inventory/{product_id}",
    response_model=InventoryEntry,
    tags=["inventory"],
)
async def update_product_inventory(
    product_id: int,
    update: InventoryUpdateRequest,
) -> InventoryEntry:
    \"\"\"Update inventory level for a product.\"\"\"
    async with get_db_session() as db:
        await db.execute(
            "UPDATE inventory SET quantity = quantity + :delta WHERE product_id = :id",
            {"delta": update.quantity_delta, "id": product_id},
        )
        row = await db.fetch_one(
            "SELECT product_id, warehouse_id, quantity, reserved FROM inventory "
            "WHERE product_id = :product_id",
            {"product_id": product_id},
        )
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )
        return InventoryEntry(**dict(row))
"""

TASK5_SCHEMAS_C001_OURS = """\
class CategoryResponse(BaseModel):
    \"\"\"Response schema for a single product category.\"\"\"

    id: int
    name: str
    slug: str
    active: bool


class CategoryListResponse(BaseModel):
    \"\"\"Paginated list of categories.\"\"\"

    categories: List[CategoryResponse]
    total: int


class ProductResponse(BaseModel):
    \"\"\"Response schema for a single product.\"\"\"

    id: int
    name: str
    sku: str
    price: float = Field(..., ge=0, description="Unit price in USD")
    category_id: int
    in_stock: bool

    @field_validator("price")
    @classmethod
    def price_must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("price must be non-negative")
        return round(v, 2)


class ProductListResponse(BaseModel):
    \"\"\"Paginated list of products.\"\"\"

    products: List[ProductResponse]
    page: int
    page_size: int


class ProductCreateRequest(BaseModel):
    \"\"\"Request body for creating a new product.\"\"\"

    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=50, pattern=r"^[A-Z0-9\\-]+$")
    price: float = Field(..., ge=0)
    category_id: int
    in_stock: bool = True


class ErrorResponse(BaseModel):
    \"\"\"Standard error response body.\"\"\"

    detail: str
    status_code: int
"""
TASK5_SCHEMAS_C001_THEIRS = """\
# v1 had no formal schemas — responses were raw dicts.
# Developer B added these new schemas for inventory tracking:

class InventoryEntry(BaseModel):
    \"\"\"Represents a warehouse inventory record for a product.\"\"\"

    product_id: int
    warehouse_id: str
    quantity: int = Field(..., ge=0)
    reserved: int = Field(default=0, ge=0)

    @property
    def available(self) -> int:
        \"\"\"Units available for sale (total minus reserved).\"\"\"
        return self.quantity - self.reserved


class InventoryUpdateRequest(BaseModel):
    \"\"\"Request body for updating inventory levels.\"\"\"

    warehouse_id: str
    quantity_delta: int
    reason: str = Field(..., min_length=1, max_length=500)
"""
TASK5_SCHEMAS_C001_GT = """\
class CategoryResponse(BaseModel):
    \"\"\"Response schema for a single product category.\"\"\"

    id: int
    name: str
    slug: str
    active: bool


class CategoryListResponse(BaseModel):
    \"\"\"Paginated list of categories.\"\"\"

    categories: List[CategoryResponse]
    total: int


class ProductResponse(BaseModel):
    \"\"\"Response schema for a single product.\"\"\"

    id: int
    name: str
    sku: str
    price: float = Field(..., ge=0, description="Unit price in USD")
    category_id: int
    in_stock: bool

    @field_validator("price")
    @classmethod
    def price_must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("price must be non-negative")
        return round(v, 2)


class ProductListResponse(BaseModel):
    \"\"\"Paginated list of products.\"\"\"

    products: List[ProductResponse]
    page: int
    page_size: int


class ProductCreateRequest(BaseModel):
    \"\"\"Request body for creating a new product.\"\"\"

    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=50, pattern=r"^[A-Z0-9\\-]+$")
    price: float = Field(..., ge=0)
    category_id: int
    in_stock: bool = True


class ErrorResponse(BaseModel):
    \"\"\"Standard error response body.\"\"\"

    detail: str
    status_code: int


class InventoryEntry(BaseModel):
    \"\"\"Represents a warehouse inventory record for a product.\"\"\"

    product_id: int
    warehouse_id: str
    quantity: int = Field(..., ge=0)
    reserved: int = Field(default=0, ge=0)

    @property
    def available(self) -> int:
        \"\"\"Units available for sale (total minus reserved).\"\"\"
        return self.quantity - self.reserved


class InventoryUpdateRequest(BaseModel):
    \"\"\"Request body for updating inventory levels.\"\"\"

    warehouse_id: str
    quantity_delta: int
    reason: str = Field(..., min_length=1, max_length=500)
"""

TASK5_TESTS_C001_OURS = """\
class TestCategoriesV2:
    \"\"\"Tests for the /api/v2/categories endpoints.\"\"\"

    def test_list_categories_returns_200(self):
        response = client.get("/api/v2/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "total" in data
        assert isinstance(data["categories"], list)

    def test_get_category_not_found_returns_404(self):
        response = client.get("/api/v2/categories/99999")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_list_categories_active_filter(self):
        response = client.get("/api/v2/categories?active_only=false")
        assert response.status_code == 200
"""
TASK5_TESTS_C001_THEIRS = """\
class TestCategoriesV1:
    \"\"\"Tests for the /api/v1/categories endpoints.\"\"\"

    def test_list_categories_returns_200(self):
        response = client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)

    def test_get_category_not_found_returns_404(self):
        response = client.get("/api/v1/categories/99999")
        assert response.status_code == 404

    def test_list_categories_active_filter(self):
        response = client.get("/api/v1/categories?active_only=false")
        assert response.status_code == 200


class TestProductsV1:
    \"\"\"Tests for the v1 product endpoints added by Developer B.\"\"\"

    def test_list_products_returns_200(self):
        response = client.get("/api/v1/products")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "page" in data

    def test_list_products_filter_by_category(self):
        response = client.get("/api/v1/products?category_id=1")
        assert response.status_code == 200

    def test_create_product_returns_201(self):
        payload = {
            "name": "Widget Pro",
            "sku": "WGT-001",
            "price": 29.99,
            "category_id": 1,
            "in_stock": True,
        }
        response = client.post("/api/v1/products", json=payload)
        assert response.status_code == 201
        assert "id" in response.json()
"""
TASK5_TESTS_C001_GT = """\
class TestCategoriesV2:
    \"\"\"Tests for the /api/v2/categories endpoints.\"\"\"

    def test_list_categories_returns_200(self):
        response = client.get("/api/v2/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "total" in data
        assert isinstance(data["categories"], list)

    def test_get_category_not_found_returns_404(self):
        response = client.get("/api/v2/categories/99999")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_list_categories_active_filter(self):
        response = client.get("/api/v2/categories?active_only=false")
        assert response.status_code == 200


class TestInventoryV2:
    \"\"\"Tests for the /api/v2/products/inventory endpoints.\"\"\"

    def test_get_inventory_returns_200(self):
        response = client.get("/api/v2/products/inventory/1")
        assert response.status_code == 200
        data = response.json()
        assert "product_id" in data
        assert "quantity" in data
        assert "reserved" in data

    def test_get_inventory_not_found_returns_404(self):
        response = client.get("/api/v2/products/inventory/99999")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_update_inventory_returns_200(self):
        payload = {
            "warehouse_id": "WH-001",
            "quantity_delta": 10,
            "reason": "Restock from supplier shipment",
        }
        response = client.patch("/api/v2/products/inventory/1", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "product_id" in data
        assert "quantity" in data
"""


def get_task5() -> dict:
    """Return the task definition for multi_file_api_overhaul."""
    conflict_blocks = [
        ConflictBlock(
            conflict_id="conflict_001",
            file_path="api/routes.py",
            ours_content=TASK5_ROUTES_C001_OURS,
            theirs_content=TASK5_ROUTES_C001_THEIRS,
            surrounding_context_before=(
                "from __future__ import annotations\n\n"
                "from typing import List, Optional\n"
            ),
            surrounding_context_after="\nrouter = APIRouter()\n\n",
            ours_branch_name="main",
            theirs_branch_name="feature/product-catalog-v2",
        ),
        ConflictBlock(
            conflict_id="conflict_002",
            file_path="api/routes.py",
            ours_content=TASK5_ROUTES_C002_OURS,
            theirs_content=TASK5_ROUTES_C002_THEIRS,
            surrounding_context_before="router = APIRouter()\n\n",
            surrounding_context_after=(
                "\n@router.get(\n"
                "    \"/api/v2/products\",\n"
                "    response_model=ProductListResponse,\n"
                "    tags=[\"products\"],\n"
                ")\n"
            ),
            ours_branch_name="main",
            theirs_branch_name="feature/product-catalog-v2",
        ),
        ConflictBlock(
            conflict_id="conflict_003",
            file_path="api/schemas.py",
            ours_content=TASK5_SCHEMAS_C001_OURS,
            theirs_content=TASK5_SCHEMAS_C001_THEIRS,
            surrounding_context_before=(
                "from typing import List, Optional\n"
                "from pydantic import BaseModel, Field, field_validator\n\n"
            ),
            surrounding_context_after="",
            ours_branch_name="main",
            theirs_branch_name="feature/product-catalog-v2",
        ),
        ConflictBlock(
            conflict_id="conflict_004",
            file_path="tests/test_api.py",
            ours_content=TASK5_TESTS_C001_OURS,
            theirs_content=TASK5_TESTS_C001_THEIRS,
            surrounding_context_before=(
                "from api.main import app\n\nclient = TestClient(app)\n\n\n"
            ),
            surrounding_context_after=(
                "\n\nclass TestProductsV2:\n"
                "    \"\"\"Tests for the /api/v2/products endpoints.\"\"\"\n"
            ),
            ours_branch_name="main",
            theirs_branch_name="feature/product-catalog-v2",
        ),
    ]

    file_contents = {
        "api/routes.py": _TASK5_ROUTES_FILE,
        "api/schemas.py": _TASK5_SCHEMAS_FILE,
        "tests/test_api.py": _TASK5_TESTS_FILE,
    }
    ground_truths = {
        "conflict_001": TASK5_ROUTES_C001_GT,
        "conflict_002": TASK5_ROUTES_C002_GT,
        "conflict_003": TASK5_SCHEMAS_C001_GT,
        "conflict_004": TASK5_TESTS_C001_GT,
    }

    return {
        "task_id": "multi_file_api_overhaul",
        "task_description": (
            "The messiest kind of conflict — a full API overhaul happening at the same time "
            "as a feature addition. Main branch moved everything to v2: proper Pydantic response "
            "models, /api/v2/ paths, HTTPException for errors. Feature branch added inventory "
            "tracking endpoints and tests, but in the old v1 style. Three files need to be "
            "consistent: routes.py, schemas.py, and the tests. New endpoints need to follow "
            "the v2 pattern or the whole thing is inconsistent."
        ),
        "difficulty": "hard",
        "conflict_blocks": conflict_blocks,
        "file_contents": file_contents,
        "ground_truths": ground_truths,
        "ours_commit_message": "refactor!: overhaul API to v2 — Pydantic response models, v2 paths, standardized errors",
        "theirs_commit_message": "feat: add inventory tracking endpoints and schemas for warehouse management",
        "max_steps": 15,
    }
