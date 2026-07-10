import os
from typing import Optional
# pyrefly: ignore [missing-import]
from motor.motor_asyncio import AsyncIOMotorClient
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

def _get_escaped_uri(uri: Optional[str]) -> Optional[str]:
    if not uri:
        return uri
    try:
        parsed = urllib.parse.urlparse(uri)
        if parsed.username or parsed.password:
            username = urllib.parse.quote_plus(urllib.parse.unquote(parsed.username)) if parsed.username else ""
            password = urllib.parse.quote_plus(urllib.parse.unquote(parsed.password)) if parsed.password else ""
            netloc = ""
            if username:
                netloc += username
                if password:
                    netloc += f":{password}"
                netloc += "@"
            host_part = parsed.netloc.split("@")[-1]
            netloc += host_part
            parsed = parsed._replace(netloc=netloc)
            return urllib.parse.urlunparse(parsed)
    except Exception:
        pass
    return uri

raw_uri = os.getenv("MONGODB_URL") or os.getenv("MONGO_URL")
MONGODB_URL = _get_escaped_uri(raw_uri)
DATABASE_NAME = os.getenv("DATABASE_NAME", "items")

class Database:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    def connect(self):
        self.client = AsyncIOMotorClient(MONGODB_URL)
        self.db = self.client[DATABASE_NAME]

    def disconnect(self):
        if self.client:
            self.client.close()

db_helper = Database()
