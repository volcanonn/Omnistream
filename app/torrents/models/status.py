from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

class JobStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    PROCESSING = "processing"

class MediaResponse(BaseModel):
    """
    Standard response model for media identification.
    """
    model_config = ConfigDict(populate_by_name=True)

    # --- Required Fields ---
    status: JobStatus = Field(..., description="Current status of the processing job")
    unique_id: str = Field(..., description="The unique identifier (MediaInfo UID or Internal ID)")

    # --- Optional Fields ---
    imdb_id: Optional[str] = Field(None, description="IMDb ID (e.g. 'tt1234567'). Optional if unknown.")
    torrent_hash: Optional[str] = Field(None, description="SHA256 Info Hash of the torrent")
    index: Optional[int] = Field(None, description="File index within the torrent structure")