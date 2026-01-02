from fastapi import APIRouter, HTTPException
from . import services, models

router = APIRouter(prefix="/torrents")

@router.post("/create/", response_model=models.User)
def create_new_media(user: models.UserCreate):
    """
    Endpoint to create a new media.
    """
    # The 'user' parameter is a UserCreate Pydantic model.
    # FastAPI automatically validates the incoming request body.
    new_user = services.create_user(user=user)
    return new_user

@router.get("/users/{user_id}", response_model=models.User)
def read_user(user_id: int):
    """
    Endpoint to get a user by their ID.
    """
    db_user = services.get_user(user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user