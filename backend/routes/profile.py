from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from auth.dependencies import get_current_user
from config.database import get_session
from models.db_models import User, UserProfile
from models.schemas import ProfileResponse, ProfileUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# GET /profile
# ---------------------------------------------------------------------------

@router.get("", response_model=ProfileResponse)
def get_profile(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the authenticated user's profile information.
    If no profile exists, returns a default empty profile response
    without modifying the database (READ-ONLY).
    """
    profile = db.exec(select(UserProfile).where(UserProfile.user_id == current_user.id)).first()

    if profile is None:
        return ProfileResponse(
            email=current_user.email,
            name=None,
            date_of_birth=None,
            language=None
        )
    
    return ProfileResponse(
        email=current_user.email,
        name=profile.name,
        date_of_birth=profile.date_of_birth,
        language=profile.language
    )


# ---------------------------------------------------------------------------
# PATCH /profile
# ---------------------------------------------------------------------------

@router.patch("", response_model=ProfileResponse)
def update_profile(
    request: ProfileUpdateRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Partially updates the authenticated user's profile.
    If the profile does not exist, it creates it using the supplied values.
    """
    profile = db.exec(select(UserProfile).where(UserProfile.user_id == current_user.id)).first()

    # Create profile if it doesn't exist
    if profile is None:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    # Update provided fields (partial update)
    update_data = request.model_dump(exclude_unset=True)
    
    if "name" in update_data:
        profile.name = update_data["name"]
    if "date_of_birth" in update_data:
        profile.date_of_birth = update_data["date_of_birth"]
    if "language" in update_data:
        profile.language = update_data["language"]
        
    profile.updated_at = datetime.now(timezone.utc)

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return ProfileResponse(
        email=current_user.email,
        name=profile.name,
        date_of_birth=profile.date_of_birth,
        language=profile.language
    )