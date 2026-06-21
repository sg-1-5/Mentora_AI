from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import MONGODB_URL

client: AsyncIOMotorClient | None = None
db = None

async def connect_to_mongo():
    global client, db
    if not client:
        client = AsyncIOMotorClient(MONGODB_URL)
        try:
            # Verify connection
            await client.admin.command('ping')
            db = client.get_default_database()
            print("MongoDB connected successfully")
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            db = None

async def close_mongo():
    global client
    if client:
        client.close()
        print("MongoDB connection closed")
