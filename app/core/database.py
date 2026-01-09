import redis.asyncio as redis
import os
from redis.exceptions import ConnectionError

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.Redis(
    host=REDIS_HOST, 
    port=REDIS_PORT, 
    db=0,
    decode_responses=False
)

"""class RedisManager:
    def __init__(self):
        self.redis_client: redis.Redis | None = None

        self.connected_event = asyncio.Event()

    async def connect(self):
        print("connecting now")
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))

        print("Attempting to connect to DragonflyDB...")

        self.redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            db=0,
            decode_responses=False
        )

        try:
            await self.redis_client.ping()
            self.connected_event.set()
            print(f"Successfully connected to DragonflyDB at {redis_host}:{redis_port}")
        except ConnectionError as e:
            print(f"FATAL: Could not connect to DragonflyDB. Please check the connection. Error: {e}")

    async def close(self):
        if self.redis_client:
            await self.redis_client.close()
            print("Redis connection closed.")

    async def get_client(self) -> redis.Redis:
        if not self.connected_event.is_set():
            print("🛑 Request waiting for DB connection...")
            await self.connected_event.wait()
        
        return self.redis_client

db = RedisManager()
"""