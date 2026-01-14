from __future__ import annotations
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class MetaAttributes(BaseModel):
    """
    Metadata inside the attributes block.
    """
    poster: Optional[str] = Field(None, description="URL to the poster image")
    genres: Optional[str] = Field(None, description="Comma separated string of genres or null")

class TorrentFile(BaseModel):
    """
    Represents an individual file inside the torrent.
    """
    id: int
    name: str
    size: int

class Unit3dAttributes(BaseModel):
    """
    The core data block for the torrent.
    """
    model_config = ConfigDict(populate_by_name=True)

    # --- Basic Info ---
    name: str
    meta: MetaAttributes
    release_year: Optional[int] = None
    category: str = Field(description="e.g. Movie, TV")
    type: str = Field(description="e.g. WEB-DL, BluRay")
    resolution: Optional[str] = Field(None, description="e.g. 1080p, 2160p")

    # --- Technical Info ---
    # Note: media_info and bd_info are often returned as raw text blocks, not parsed JSON.
    media_info: Optional[str] = Field(None, description="Raw MediaInfo text output")
    bd_info: Optional[str] = Field(None, description="Raw BDInfo text output")
    description: Optional[str] = Field(None, description="HTML or BBCode description")
    
    # --- Torrent Specifics ---
    info_hash: str
    size: int = Field(description="Total size in bytes")
    num_file: int
    files: List[TorrentFile] = Field(default_factory=list)

    # --- Status & Flags ---
    # 'freeleech' is typically returned as a string percentage "0%" or "100%" in UNIT3D
    freeleech: Optional[str] = Field(None, description="e.g. '0%', '100%'") 
    double_upload: bool
    refundable: bool
    internal: bool
    trumpable: bool
    exclusive: bool
    featured: bool
    personal_release: bool
    
    # --- Stats ---
    uploader: Optional[str] = None
    seeders: int
    leechers: int
    times_completed: int

    # --- External IDs (Nullable) ---
    tmdb_id: Optional[int] = None
    imdb_id: Optional[int] = None
    tvdb_id: Optional[int] = None
    mal_id: Optional[int] = None
    igdb_id: Optional[int] = None

    # --- Internal IDs ---
    category_id: int
    type_id: int
    resolution_id: int

    # --- Timestamps & Links ---
    created_at: datetime
    details_link: str
    download_link: str
    magnet_link: Optional[str] = None

class Unit3dTorrent(BaseModel):
    """
    Root model for a single UNIT3D torrent response.
    Follows JSON:API spec (type, id, attributes).
    """
    type: str = Field(..., description="Should be 'torrent'")
    id: str = Field(..., description="The internal tracker ID (returned as string)")
    attributes: Unit3dAttributes