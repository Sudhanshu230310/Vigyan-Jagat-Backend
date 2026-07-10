from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
# pyrefly: ignore [missing-import]
from bson import ObjectId
from db.connection import db_helper

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


@app.get("/")
async def read_root():
    """
    Root endpoint that provides API status and list of items in the database.
    """
    items_list = []
    if db_helper.db is not None:
        cursor = db_helper.db.items.find()
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


@app.get("/items/{item_id}")
async def read_item(item_id: str, q: Optional[str] = None):
    """
    Retrieve an item by its ID. Supports optional query filtering.
    """
    try:
        obj_id = ObjectId(item_id)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid item ID format: '{item_id}'. Must be a valid 24-character hex string."
        )
    
    if db_helper.db is None:
        raise HTTPException(
            status_code=500,
            detail="Database connection not initialized"
        )
        
    item = await db_helper.db.items.find_one({"_id": obj_id})
    if not item:
        raise HTTPException(
            status_code=404, 
            detail=f"Item with ID {item_id} not found"
        )
    

    item_data = item.copy()
    item_data.pop("_id", None)
    
    response = {
        "item_id": item_id,
        "item": item_data
    }
    if q:
        response.update({"query": q})
    return response


@app.get("/{category}")
async def read_root(category: str):
    items_list = []
    if db_helper.db is not None:
        cursor = db_helper.db.items.find({f"category": category})
        async for doc in cursor:
            doc_copy = doc.copy()
            doc_copy["_id"] = str(doc_copy["_id"])
            items_list.append(doc_copy)
    
    return {
        "items": items_list,
    }




