from fastapi import APIRouter, HTTPException
from . import services, models

router = APIRouter(prefix="/torrents")

@router.post("/create/", response_model=models.User)
def create_new_media(json_media: models.MediaInfoSummary):
    """
    Endpoint to create a new media.
    """
    services.create_media_summary(json_media)
    

@router.get("/users/{user_id}", response_model=models.User)
def read_user(user_id: int):
    """
    Endpoint to get a user by their ID.
    """
    db_user = services.get_user(user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user