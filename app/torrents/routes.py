from fastapi import APIRouter, Depends, HTTPException
from .models import *
from .services import *

router = APIRouter(prefix="/torrents")

@router.post("/upload", response_model=CreateMediaResponse)
async def create_mediainfo_json(json_media: MediaInfoFile):
    """
    Endpoint to create a new media.
    """
    response = await create_media_summary_from_mediainfo(json_media)
    return response

@router.post("/upload/tracker", response_model=CreateMediaResponse)
async def create_mediainfo_text(json_media: Unit3dTorrent):
    """
    Endpoint to create a new media with tracker data.
    """
    response = await create_media_summary_from_tracker(json_media)
    return response

@router.post("/media", response_model=MediaDataResponse)
async def get_mediainfo_json(params: MediaRequestParams):
    """
    Endpoint to get mediainfo.
    """
    response = await process_lookup(params)
    return response

@router.get("/media", response_model=MediaDataResponse)
async def search_mediainfo_json(params: MediaRequestParams = Depends()):
    """
    Endpoint to get mediainfo.
    """
    response = await process_lookup(params)
    return response
