"""Refinement endpoint — hybrid LLM intent parsing + deterministic slot-filling."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Activity
from app.api.schemas import RefineRequest, RefineResponse
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/refine-itinerary", response_model=RefineResponse)
async def refine_itinerary(
    request: RefineRequest,
    db: Session = Depends(get_db),
):
    """
    Refine an existing itinerary using a natural language request.

    Flow:
    1. LLM parses user's intent into structured RefinementIntent JSON
    2. Backend validates LLM suggestions against real DB activities
    3. If invalid → semantic RAG fallback to find best candidates
    4. Deterministic slot-filler applies changes using scoring.py
    5. Returns updated itinerary + explanation of changes made

    Example requests:
    - "Replace the museum on Day 2 with something for nightlife"
    - "Add a food experience in the evening on Day 1"
    - "Remove the adventure activity from Day 3"
    - "Swap Day 2 morning with something cheaper"
    """
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="LLM not configured — OPENAI_API_KEY missing")

    from app.services.refinement_service import parse_refinement_intent, apply_refinement

    preferences = request.preferences
    itinerary = request.itinerary
    user_message = request.user_message

    # Determine city ID for candidate pool
    city_id = preferences.destination_city_id
    if not city_id and preferences.city_segments:
        city_id = preferences.city_segments[0].city_id

    if not city_id:
        raise HTTPException(status_code=400, detail="Could not determine city from preferences")

    # Build candidate pool from DB (compact, for LLM prompt)
    all_activities = db.query(Activity).filter(Activity.city_id == city_id).all()
    candidate_pool = [
        {"name": a.name, "category": a.category, "cost": a.base_cost}
        for a in all_activities
    ]

    # Step 1: Parse intent with LLM
    try:
        intent = await parse_refinement_intent(user_message, itinerary, candidate_pool)
        logger.info(f"Parsed refinement intent: action={intent.action}, day={intent.target_day}, target={intent.target_activity_name}")
    except Exception as e:
        logger.error(f"LLM intent parsing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse refinement request: {str(e)}")

    # Step 2: Apply refinement deterministically
    try:
        result = await apply_refinement(intent, itinerary, preferences, db, user_message=user_message)
        return result
    except Exception as e:
        logger.error(f"Refinement application failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply refinement: {str(e)}")
