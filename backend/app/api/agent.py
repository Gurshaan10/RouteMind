"""Agent planning endpoint — OpenAI function calling orchestration."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.schemas import AgentPlanRequest, AgentPlanResponse
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/agent-plan", response_model=AgentPlanResponse)
async def agent_plan(
    request: AgentPlanRequest,
    db: Session = Depends(get_db),
):
    """
    Plan an itinerary using an AI agent with tool calling.

    Unlike /plan-itinerary which runs a fixed pipeline, this endpoint uses an
    OpenAI function-calling agent that autonomously decides how to research
    and plan the trip by calling tools (semantic search, filtering, travel time
    estimation) before invoking the deterministic optimizer.

    The full agent_trace is returned showing every tool the agent called and
    why — making the reasoning process transparent and auditable.

    Note: This endpoint is more expensive (multiple LLM calls) and slower
    than /plan-itinerary. Use it for portfolio demos or when you want to
    show agentic reasoning.
    """
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="LLM not configured — OPENAI_API_KEY missing")

    preferences = request.preferences

    city_id = preferences.destination_city_id
    if not city_id and preferences.city_segments:
        city_id = preferences.city_segments[0].city_id

    if not city_id:
        raise HTTPException(status_code=400, detail="destination_city_id or city_segments required")

    from app.services.agent_service import run_agent
    try:
        result = await run_agent(preferences, db)
        return result
    except Exception as e:
        logger.error(f"Agent planning failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent planning failed: {str(e)}")
