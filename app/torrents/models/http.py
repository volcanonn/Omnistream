from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, model_validator, ConfigDict
from .OmnistreamMetadata import OmnistreamMetadata

class JobStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    PROCESSING = "processing"

class CreateMediaResponse(BaseModel):
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

class MediaDataResponse(BaseModel):
    """
    The standardized response for a GET request.
    Wraps the 'dict' (MediaInfoSummary) in a status envelope.
    """
    model_config = ConfigDict(populate_by_name=True)

    status: JobStatus = Field(..., description="API Status")
    
    data: Optional[List[OmnistreamMetadata]] = Field(
        None, 
        description="A list of media summaries. Can be multiple items."
    )
    
    # Optional error message if status is failed
    error: Optional[str] = Field(None, description="Error details if any")

class MediaRequestParams(BaseModel):
    """
    Input parameters for identifying media.
    """
    model_config = ConfigDict(extra='forbid') 

    unique_id: Optional[str] = Field(None, description="The 128-bit MediaInfo UniqueID")
    imdb_id: Optional[str] = Field(None, description="IMDb ID (e.g., tt1234567)")
    torrent_hash: Optional[str] = Field(None, description="SHA256 Info Hash of the torrent")
    index: Optional[int] = Field(None, description="File index within the torrent")

    @model_validator(mode='after')
    def validate_identifiers(self):
        """
        Enforce logical requirements:
        1. 'index' cannot be provided without 'torrent_hash'.
        2. At least one identification method (Unique ID, IMDb, or Torrent Hash) must be present.
        """
        
        # Rule 1: Orphaned Index Check
        # You cannot ask for "file #2" if you don't say which torrent it belongs to.
        if self.index is not None and self.torrent_hash is None:
            raise ValueError("You cannot provide 'index' without 'torrent_hash'.")

        # Rule 2: Existence Check
        # User must provide at least one of the main identifiers.
        has_unique = self.unique_id is not None
        has_imdb = self.imdb_id is not None
        has_hash = self.torrent_hash is not None

        if not (has_unique or has_imdb or has_hash):
            raise ValueError(
                "No valid identifier found. You must provide either: "
                "1. 'unique_id', 2. 'imdb_id', or 3. 'torrent_hash'."
            )

        return self