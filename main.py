from fastapi import FastAPI
import asyncio
from app.core.database import redis_client
from contextlib import asynccontextmanager
from app.torrents.routes import router as torrents_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    while True:
        try:
            await redis_client.ping()
            print("DragonflyDB Connected!")
            break
        except Exception:
            print("DragonflyDB not ready. Retrying in 2s...")
            await asyncio.sleep(2)
    
    yield

    await redis_client.close()

app = FastAPI(
    title="CinephileDB",
    description="A high-speed movie media info database.",
    lifespan=lifespan
)

app.include_router(torrents_router, prefix="/api/v1", tags=["Torrents"])

@app.get("/api/v1/health", tags=["Health"])
def read_root():
    """A simple health check endpoint."""
    return {"status": "ok"}