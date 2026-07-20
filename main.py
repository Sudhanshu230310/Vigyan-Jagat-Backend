from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from urllib.parse import unquote
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
# pyrefly: ignore [missing-import]
from bson import ObjectId
from db.connection import db_helper
from db.postgres import pg_db
from datetime import datetime, timezone

class QuoteRequest(BaseModel):
    name: str
    email: str
    phone: str
    organization: str
    quantity: str
    message: str
    product_name: str
    subcategory_name: str
    brand: Optional[str] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_helper.connect()
    await pg_db.connect()
    yield
    db_helper.disconnect()
    await pg_db.disconnect()

app = FastAPI(
    title="FastAPI Simple Backend",
    description="A simple, clean, and robust backend API built with FastAPI.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {
        "status": "online",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "chemical-api"
    }


@app.post("/quote")
async def create_quote(quote: QuoteRequest):
    if not pg_db.is_connected():
        raise HTTPException(status_code=503, detail="PostgreSQL database unavailable")
        
    try:
        created_quote = await pg_db.wholesalequote.create(
            data={
                "name": quote.name,
                "email": quote.email,
                "phone": quote.phone,
                "organization": quote.organization,
                "quantity": quote.quantity,
                "message": quote.message,
                "product_name": quote.product_name,
                "subcategory_name": quote.subcategory_name,
                "brand": quote.brand,
            }
        )
        return {"status": "success", "quote_id": created_quote.id}
    except Exception as e:
        print(f"Error saving quote using Prisma: {e}")
        raise HTTPException(status_code=500, detail="Failed to save wholesale quote request")


@app.get("/product/{subcategory}/{name}")
async def read_single_product(subcategory: str, name: str):
    subcategory = unquote(subcategory)
    name = unquote(name)
 
    # Distinguish "DB not connected" (503) from "product genuinely missing" (404).
    if db_helper.db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
 
    cursor = db_helper.db.items.find()
    async for doc in cursor:
        products = doc.get("products", {})
        for category, subcats in products.items():
            if subcategory in subcats and name in subcats[subcategory]:
                details = subcats[subcategory][name]
                return {
                    "product": {
                        "name": name,
                        "category": category,
                        "subcategory": subcategory,
                        **details,  # brand, description, specifications, images, pages
                    }
                }
 
    raise HTTPException(status_code=404, detail="Product not found")


@app.get("/category/{category}/subcategories")
async def read_subcategories(category: str):
    category = unquote(category)
 
    # Distinguish "DB not connected" (503) from "category genuinely missing" (404).
    if db_helper.db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
 
    subcategories = set()
    cursor = db_helper.db.items.find()
    async for doc in cursor:
        products = doc.get("products", {})
        if category in products:
            subcategories.update(products[category].keys())
 
    if not subcategories:
        raise HTTPException(status_code=404, detail="Category not found")
 
    return {
        "category": category,
        "subcategories": sorted(subcategories),
    }


@app.get("/{subcategory:path}")
async def read_by_subcategory(subcategory: str):
    subcategory = unquote(subcategory)
    items_list = []
    if db_helper.db is not None:
        cursor = db_helper.db.items.find()
        async for doc in cursor:
            products = doc.get("products", {})
            for category, subcats in products.items():
                if subcategory in subcats:
                    for name, details in subcats[subcategory].items():
                        items_list.append({
                            "name": name,
                            "brand": details.get("brand"),
                            "description": details.get("description"),
                        })
    return {"items": items_list}