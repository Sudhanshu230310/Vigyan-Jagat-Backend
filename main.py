from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from urllib.parse import unquote
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
# pyrefly: ignore [missing-import]
from bson import ObjectId
from db.connection import db_helper
from datetime import datetime, timezone

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_helper.connect()
    yield
    db_helper.disconnect()

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