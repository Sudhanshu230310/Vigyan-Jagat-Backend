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
    """
    Root endpoint that provides API status and list of items in the database.
    """
    items_list = []
    if db_helper.db is not None:
        cursor = db_helper.db.items.find()
        print(cursor)
        async for doc in cursor:
            doc_copy = doc.copy()
            doc_copy["_id"] = str(doc_copy["_id"])
            items_list.append(doc_copy)
    
    return {
        "items": items_list,
        "status": "online",
        "message": "Welcome to the FastAPI Simple Backend!",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
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