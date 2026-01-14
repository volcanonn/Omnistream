from fastapi import APIRouter, HTTPException
from .models import *
from .services import *

router = APIRouter(prefix="/torrents")

@router.post("/create") #, response_model=models.User
async def create_mediainfo_json(json_media: MediaInfoFile):
    """
    Endpoint to create a new media.
    """
    await create_media_summary_from_mediainfo(json_media)

@router.post("/create/tracker") #, response_model=models.User
async def create_mediainfo_text(json_media: Unit3dTorrent):
    """
    Endpoint to create a new media with tracker data.
    """
    await create_media_summary_from_tracker(json_media)
