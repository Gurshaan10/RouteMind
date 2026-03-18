"""RAG retrieval service for semantic activity search using pgvector."""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.api.schemas import TripPreferences
from app.db.models import Activity, ActivityEmbedding
from app.services.embedding_service import (
    build_preference_query_text,
    generate_embedding,
)

logger = logging.getLogger(__name__)


async def retrieve_activities_semantic(
    preferences: TripPreferences,
    city_id: int,
    db: Session,
    top_k: Optional[int] = None,
) -> List[Activity]:
    """
    Retrieve the most semantically relevant activities for a city given user preferences.

    Steps:
    1. Build a semantic query string from preferences
    2. Embed the query using OpenAI text-embedding-3-small
    3. Run cosine similarity search against activity_embeddings using pgvector
    4. Return the top-K Activity ORM objects

    Falls back to full SQL if:
    - RAG is disabled in settings
    - pgvector extension not available
    - No embeddings exist for this city
    - Any error during embedding/retrieval
    """
    if top_k is None:
        top_k = settings.RAG_TOP_K

    # Build categories list
    categories = [cat.value for cat in preferences.preferred_categories] if preferences.preferred_categories else []

    # Build constraints description
    constraints_text = None
    if preferences.constraints:
        parts = []
        if preferences.constraints.must_visit:
            parts.append(f"Must include: {', '.join(preferences.constraints.must_visit)}")
        if preferences.constraints.avoid:
            parts.append(f"Avoid: {', '.join(preferences.constraints.avoid)}")
        if preferences.constraints.dietary_preferences:
            parts.append(f"Dietary: {preferences.constraints.dietary_preferences}")
        if parts:
            constraints_text = ". ".join(parts)

    # Check if any embeddings exist for this city
    has_embeddings = (
        db.query(ActivityEmbedding)
        .join(Activity, ActivityEmbedding.activity_id == Activity.id)
        .filter(Activity.city_id == city_id)
        .first()
    )

    if not has_embeddings:
        logger.info(f"No embeddings found for city {city_id}, falling back to full SQL retrieval")
        return _fallback_sql(city_id, db)

    try:
        query_text = build_preference_query_text(
            trip_type=preferences.trip_type.value,
            energy_level=preferences.energy_level.value,
            categories=categories,
            budget_level=preferences.budget_level.value,
            constraints_text=constraints_text,
        )

        query_embedding = await generate_embedding(query_text)

        # Format embedding as pgvector literal: '[0.1, 0.2, ...]'
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        # Cosine similarity search: <=> operator returns cosine distance (lower = more similar)
        sql = text("""
            SELECT a.id, ae.embedding_vec <=> CAST(:embedding AS vector) AS distance
            FROM activity_embeddings ae
            JOIN activities a ON ae.activity_id = a.id
            WHERE a.city_id = :city_id
              AND ae.embedding_vec IS NOT NULL
            ORDER BY distance ASC
            LIMIT :top_k
        """)

        rows = db.execute(sql, {
            "embedding": embedding_str,
            "city_id": city_id,
            "top_k": top_k,
        }).fetchall()

        if not rows:
            logger.warning(f"pgvector query returned 0 results for city {city_id}, falling back")
            return _fallback_sql(city_id, db)

        activity_ids = [row[0] for row in rows]
        activities = db.query(Activity).filter(Activity.id.in_(activity_ids)).all()

        # Preserve ranking order from pgvector
        id_order = {aid: idx for idx, aid in enumerate(activity_ids)}
        activities.sort(key=lambda a: id_order.get(a.id, 999))

        logger.info(f"RAG retrieved {len(activities)} candidates for city {city_id} (top_k={top_k})")
        return activities

    except Exception as e:
        logger.error(f"RAG retrieval failed for city {city_id}: {e}. Falling back to SQL.")
        return _fallback_sql(city_id, db)


def _fallback_sql(city_id: int, db: Session) -> List[Activity]:
    """Full SQL fallback — returns all activities for the city."""
    activities = db.query(Activity).filter(Activity.city_id == city_id).all()
    logger.info(f"SQL fallback: retrieved {len(activities)} activities for city {city_id}")
    return activities
