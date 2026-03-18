"""Server-Sent Events (SSE) for streaming AI responses."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.schemas import TripPreferences
from app.core.session import get_session_id
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


async def stream_itinerary_generation(
    preferences: TripPreferences,
    session_id: str,
    db: Session
):
    """
    Stream itinerary generation progress as Server-Sent Events.

    Yields progress updates:
    - Fetching activities
    - Running optimization
    - Generating narrative
    - Final result
    """
    try:
        # Step 1: Fetch activities
        yield f"data: {json.dumps({'step': 'fetching', 'message': 'Fetching activities...', 'progress': 20})}\n\n"
        await asyncio.sleep(0.1)  # Allow client to receive

        # Import here to avoid circular imports
        from app.services.itinerary_planner import ItineraryPlanner
        from app.db.models import City, Activity

        # Get city
        city = db.query(City).filter(City.id == preferences.destination_city_id).first()
        if not city:
            yield f"data: {json.dumps({'step': 'error', 'message': 'City not found'})}\n\n"
            return

        yield f"data: {json.dumps({'step': 'city_found', 'message': f'Planning trip to {city.name}', 'progress': 30})}\n\n"
        await asyncio.sleep(0.1)

        # Get activities
        activities = db.query(Activity).filter(Activity.city_id == city.id).all()
        yield f"data: {json.dumps({'step': 'activities', 'message': f'Found {len(activities)} activities', 'progress': 40})}\n\n"
        await asyncio.sleep(0.1)

        # Step 2: Run optimizer
        yield f"data: {json.dumps({'step': 'optimizing', 'message': 'Optimizing your itinerary...', 'progress': 50})}\n\n"
        await asyncio.sleep(0.1)

        planner = ItineraryPlanner(db)

        # Note: This is synchronous, but we wrap it for streaming
        # In a real implementation, you'd make the planner async or use run_in_executor
        itinerary = planner.plan_itinerary(preferences)

        yield f"data: {json.dumps({'step': 'optimized', 'message': 'Itinerary optimized!', 'progress': 70})}\n\n"
        await asyncio.sleep(0.1)

        # Step 3: Generate narrative (if using AI)
        yield f"data: {json.dumps({'step': 'narrative', 'message': 'Generating travel narrative...', 'progress': 80})}\n\n"
        await asyncio.sleep(0.5)  # Simulate AI processing

        yield f"data: {json.dumps({'step': 'narrative_done', 'message': 'Narrative ready!', 'progress': 90})}\n\n"
        await asyncio.sleep(0.1)

        # Step 4: Send final result
        yield f"data: {json.dumps({'step': 'complete', 'message': 'Itinerary generated!', 'progress': 100, 'result': json.loads(itinerary.model_dump_json())})}\n\n"

    except Exception as e:
        logger.error(f"Error streaming itinerary: {e}")
        yield f"data: {json.dumps({'step': 'error', 'message': str(e)})}\n\n"


@router.post("/plan-itinerary/stream")
async def stream_plan_itinerary(
    preferences: TripPreferences,
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
):
    """
    Stream itinerary generation with real-time progress updates.

    Returns Server-Sent Events (SSE) with progress information.
    """
    return StreamingResponse(
        stream_itinerary_generation(preferences, session_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
