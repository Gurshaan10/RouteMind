"""
Agent orchestration service using OpenAI function calling.

The agent decides which tools to call to build a trip itinerary.
All tools execute locally in Python — the LLM only decides what to call.
The deterministic optimizer validates final feasibility.

This is a portfolio-facing feature demonstrating:
- OpenAI function calling / tool use
- Agentic reasoning loops (bounded)
- Transparent reasoning via agent_trace
"""
import json
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.api.schemas import (
    TripPreferences,
    ItineraryResponse,
    ItinerarySummary,
    NarrativeResult,
    AgentToolCall,
    AgentPlanResponse,
)
from app.config import settings
from app.db.models import Activity

logger = logging.getLogger(__name__)

MAX_AGENT_TURNS = 10

# --- Tool definitions (OpenAI function calling format) ---

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_activities_semantic",
            "description": "Search for activities in a city semantically. Use this to find activities matching a vibe or theme.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city_id": {"type": "integer", "description": "The city ID to search in"},
                    "query": {"type": "string", "description": "Semantic search query, e.g. 'outdoor adventure near nature'"},
                    "top_k": {"type": "integer", "description": "Number of results to return (default 20)", "default": 20},
                },
                "required": ["city_id", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_activities",
            "description": "Filter a list of activity IDs by category, max cost, or minimum rating.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city_id": {"type": "integer", "description": "City to filter activities in"},
                    "category": {"type": "string", "description": "Category filter: food, culture, nightlife, nature, shopping, adventure, beaches"},
                    "max_cost": {"type": "number", "description": "Maximum cost per activity"},
                    "min_rating": {"type": "number", "description": "Minimum rating (0-5)"},
                    "limit": {"type": "integer", "description": "Max results to return", "default": 20},
                },
                "required": ["city_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_travel_time",
            "description": "Estimate travel time in minutes between two GPS coordinates using a travel mode.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat1": {"type": "number"},
                    "lon1": {"type": "number"},
                    "lat2": {"type": "number"},
                    "lon2": {"type": "number"},
                    "travel_mode": {"type": "string", "description": "walking, public_transport, taxi, self_drive, mixed"},
                },
                "required": ["lat1", "lon1", "lat2", "lon2", "travel_mode"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "optimize_itinerary",
            "description": "Run the deterministic optimizer to build the final itinerary from user preferences. Call this as the last step after gathering activity info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ready": {"type": "boolean", "description": "Set to true when ready to generate the final itinerary"},
                },
                "required": ["ready"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_activity",
            "description": "Get a short explanation of why an activity might be good for these preferences.",
            "parameters": {
                "type": "object",
                "properties": {
                    "activity_name": {"type": "string"},
                    "reason": {"type": "string", "description": "Why the agent thinks this activity fits"},
                },
                "required": ["activity_name", "reason"],
            },
        },
    },
]


async def run_agent(
    preferences: TripPreferences,
    db: Session,
) -> AgentPlanResponse:
    """
    Run the agent planning loop.

    The agent:
    1. Receives the user's trip preferences
    2. Calls tools to explore activities, check travel times, filter options
    3. When ready, calls optimize_itinerary to run the deterministic planner
    4. Returns the itinerary + full agent trace

    Max 10 turns to prevent runaway API costs.
    """
    from openai import AsyncOpenAI
    from app.core.optimizer import build_itinerary
    from app.core.scoring import haversine_distance, estimate_travel_time as _estimate_travel_time
    from app.llm.generator import generate_narrative
    from app.core.optimizer import Itinerary

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    city_id = preferences.destination_city_id
    if not city_id and preferences.city_segments:
        city_id = preferences.city_segments[0].city_id

    # System message: give agent context about the task
    system_message = f"""You are a travel itinerary planning agent for RouteMind.
Your job is to plan an optimal itinerary for the user's preferences.

Trip details:
- City ID: {city_id}
- Dates: {preferences.start_date} to {preferences.end_date}
- Budget: {preferences.budget_level.value}
- Energy level: {preferences.energy_level.value}
- Travel mode: {preferences.travel_mode.value}
- Preferred categories: {[c.value for c in (preferences.preferred_categories or [])]}

Strategy:
1. Use search_activities_semantic to find relevant activities
2. Use filter_activities to narrow down by constraints
3. Use estimate_travel_time if you want to check proximity between activities
4. Use explain_activity to reason about your choices (optional, good for transparency)
5. Call optimize_itinerary when you're ready to generate the final plan

Keep tool calls focused. Once you have enough information, call optimize_itinerary.
"""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": "Please plan my itinerary based on the preferences above."},
    ]

    agent_trace: list[AgentToolCall] = []
    total_tokens = 0
    final_itinerary: Optional[ItineraryResponse] = None

    # Load all activities for this city (used by tool executors)
    all_activities = db.query(Activity).filter(Activity.city_id == city_id).all() if city_id else []
    activity_by_name = {a.name: a for a in all_activities}

    for turn in range(MAX_AGENT_TURNS):
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=800,
        )

        total_tokens += response.usage.total_tokens if response.usage else 0
        choice = response.choices[0]
        messages.append({"role": "assistant", "content": choice.message.content, "tool_calls": [
            {"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in (choice.message.tool_calls or [])
        ]})

        if not choice.message.tool_calls:
            # Agent is done without calling optimize_itinerary — force it
            logger.warning("Agent stopped without calling optimize_itinerary, running optimizer now")
            break

        # Execute each tool call
        tool_results = []
        for tc in choice.message.tool_calls:
            func_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            result_str = ""

            if func_name == "search_activities_semantic":
                result_str = await _tool_search_semantic(args, city_id, db, all_activities)

            elif func_name == "filter_activities":
                result_str = _tool_filter_activities(args, city_id, db)

            elif func_name == "estimate_travel_time":
                from app.core.scoring import TravelMode
                try:
                    mode = TravelMode(args.get("travel_mode", "mixed"))
                except ValueError:
                    mode = TravelMode.mixed
                dist = haversine_distance(args["lat1"], args["lon1"], args["lat2"], args["lon2"])
                mins = _estimate_travel_time(dist, mode)
                result_str = f"{mins} minutes travel time"

            elif func_name == "optimize_itinerary":
                # This is the terminal tool — run the deterministic optimizer
                logger.info("Agent called optimize_itinerary — running planner")
                itinerary_obj = build_itinerary(preferences, all_activities, use_ortools=settings.USE_ORTOOLS)
                narrative = await generate_narrative(itinerary_obj, preferences)
                final_itinerary = ItineraryResponse(
                    days=itinerary_obj.days,
                    summary=itinerary_obj.summary or ItinerarySummary(total_cost=0, avg_cost_per_day=0, categories_covered=[], pace_label="None"),
                    optimization_score=itinerary_obj.optimization_score,
                    confidence_score=itinerary_obj.confidence_score,
                    narrative=narrative,
                )
                result_str = f"Itinerary generated: {len(itinerary_obj.days)} days planned."

            elif func_name == "explain_activity":
                result_str = f"Activity '{args.get('activity_name')}': {args.get('reason', 'Good fit for preferences.')}"

            else:
                result_str = f"Unknown tool: {func_name}"

            agent_trace.append(AgentToolCall(
                tool_name=func_name,
                arguments=args,
                result=result_str,
            ))

            tool_results.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_str,
            })

        messages.extend(tool_results)

        if final_itinerary is not None:
            break

    # If agent never called optimize_itinerary, run it now as fallback
    if final_itinerary is None:
        logger.info("Agent did not call optimize_itinerary, running as fallback")
        itinerary_obj = build_itinerary(preferences, all_activities, use_ortools=settings.USE_ORTOOLS)
        narrative = await generate_narrative(itinerary_obj, preferences)
        final_itinerary = ItineraryResponse(
            days=itinerary_obj.days,
            summary=itinerary_obj.summary or ItinerarySummary(total_cost=0, avg_cost_per_day=0, categories_covered=[], pace_label="None"),
            optimization_score=itinerary_obj.optimization_score,
            confidence_score=itinerary_obj.confidence_score,
            narrative=narrative,
        )
        agent_trace.append(AgentToolCall(
            tool_name="optimize_itinerary",
            arguments={"ready": True, "fallback": True},
            result=f"Itinerary generated as fallback: {len(itinerary_obj.days)} days planned.",
        ))

    return AgentPlanResponse(
        itinerary=final_itinerary,
        agent_trace=agent_trace,
        tokens_used=total_tokens,
    )


# --- Tool executors ---

async def _tool_search_semantic(args: dict, city_id: int, db: Session, all_activities: list) -> str:
    """Execute search_activities_semantic tool."""
    query = args.get("query", "")
    top_k = args.get("top_k", 20)
    target_city = args.get("city_id", city_id)

    if settings.RAG_ENABLED:
        try:
            from app.services.embedding_service import generate_embedding
            from sqlalchemy import text
            embedding = await generate_embedding(query)
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            rows = db.execute(text("""
                SELECT a.id, a.name, a.category, a.base_cost, a.rating
                FROM activity_embeddings ae
                JOIN activities a ON ae.activity_id = a.id
                WHERE a.city_id = :city_id AND ae.embedding_vec IS NOT NULL
                ORDER BY ae.embedding_vec <=> CAST(:embedding AS vector) ASC
                LIMIT :top_k
            """), {"city_id": target_city, "embedding": embedding_str, "top_k": top_k}).fetchall()

            results = [{"name": r[1], "category": r[2], "cost": r[3], "rating": r[4]} for r in rows]
            return json.dumps(results)
        except Exception as e:
            logger.warning(f"Agent RAG search failed: {e}, using simple filter")

    # Fallback: simple keyword/category match
    results = []
    query_lower = query.lower()
    for a in all_activities[:top_k]:
        if any(word in a.name.lower() or word in a.category.lower() for word in query_lower.split()):
            results.append({"name": a.name, "category": a.category, "cost": a.base_cost, "rating": a.rating})

    if not results:
        results = [
            {"name": a.name, "category": a.category, "cost": a.base_cost, "rating": a.rating}
            for a in all_activities[:top_k]
        ]

    return json.dumps(results)


def _tool_filter_activities(args: dict, city_id: int, db: Session) -> str:
    """Execute filter_activities tool."""
    from app.db.models import Activity
    query = db.query(Activity).filter(Activity.city_id == args.get("city_id", city_id))

    if args.get("category"):
        query = query.filter(Activity.category == args["category"])
    if args.get("max_cost") is not None:
        query = query.filter(Activity.base_cost <= args["max_cost"])
    if args.get("min_rating") is not None:
        query = query.filter(Activity.rating >= args["min_rating"])

    limit = args.get("limit", 20)
    activities = query.order_by(Activity.rating.desc()).limit(limit).all()
    results = [{"name": a.name, "category": a.category, "cost": a.base_cost, "rating": a.rating} for a in activities]
    return json.dumps(results)
