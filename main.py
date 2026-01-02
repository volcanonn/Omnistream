from fastapi import FastAPI

from app.core.database import connect_to_redis, close_redis_connection
from app.torrents.routes import router as torrents_router
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_redis()
    yield
    close_redis_connection()

app = FastAPI(
    title="CinephileDB",
    description="A high-speed movie media info database.",
    lifespan=lifespan
)

# Include the router from the movies API module
app.include_router(torrents_router, prefix="/api/v1", tags=["Torrents"])

@app.get("/api/v1/health", tags=["Health"])
def read_root():
    """A simple health check endpoint."""
    return {"status": "ok"}