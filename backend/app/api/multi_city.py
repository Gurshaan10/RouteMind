"""Multi-city trip planning API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from app.db.session import get_db
from app.services.multi_city_planner import MultiCityPlanner
from app.core.session import get_session_id
from app.core.auth import get_current_user
from app.db.models import User

router = APIRouter()


class MultiCityRequest(BaseModel):
    """Request schema for multi-city trip planning."""
    city_ids: List[int] = Field(..., min_items=2, max_items=5, description="2-5 cities to visit")
    total_days: int = Field(..., ge=4, le=30, description="Total trip duration (4-30 days)")
    budget: Optional[float] = Field(None, ge=0, description="Total budget in USD")
    interests: Optional[List[str]] = Field(
        default=None,
        description="Interest categories: food, culture, nightlife, nature, shopping, adventure, beaches"
    )
    pace: str = Field(default="moderate", description="Trip pace: relaxed, moderate, packed")


class CityRecommendationRequest(BaseModel):
    """Request schema for city recommendations."""
    base_city_id: int = Field(..., description="Starting city ID")
    num_recommendations: int = Field(default=3, ge=1, le=5, description="Number of recommendations (1-5)")
    interests: Optional[List[str]] = Field(
        default=None,
        description="Interest categories to match"
    )


@router.post("/multi-city/plan")
async def plan_multi_city_trip(
    request: MultiCityRequest,
    session_id: str = Depends(get_session_id),
    user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Plan a multi-city trip with optimized days allocation.

    Returns:
    - Suggested days per city
    - Individual itineraries for each city
    - Total cost estimate
    - Trip timeline
    - LLM narrative per city
    """
    try:
        from app.llm.generator import generate_narrative
        from app.api.routes import _check_and_increment_generation_limit

        await _check_and_increment_generation_limit(session_id, user)

        planner = MultiCityPlanner(db)

        trip_plan = planner.plan_multi_city_trip(
            city_ids=request.city_ids,
            total_days=request.total_days,
            budget=request.budget,
            interests=request.interests,
            pace=request.pace
        )

        # Generate LLM narrative for each city that was planned successfully
        for city_plan in trip_plan.get("cities", []):
            itinerary_obj = city_plan.pop("_itinerary_obj", None)
            preferences_obj = city_plan.pop("_preferences_obj", None)

            if itinerary_obj and preferences_obj:
                try:
                    narrative = await generate_narrative(itinerary_obj, preferences_obj)
                    city_plan["narrative"] = {
                        "narrative_text": narrative.narrative_text,
                        "tips": narrative.tips,
                    }
                except Exception as narrative_err:
                    import logging
                    logging.getLogger(__name__).warning(
                        f"Narrative generation failed for {city_plan.get('city_name')}: {narrative_err}"
                    )
                    city_plan["narrative"] = None

        return {
            "success": True,
            "session_id": session_id,
            "trip_plan": trip_plan
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error planning multi-city trip: {str(e)}")


@router.post("/multi-city/suggest-days")
async def suggest_days_allocation(
    city_ids: List[int],
    total_days: int,
    db: Session = Depends(get_db)
):
    """
    Get suggested days allocation for multiple cities.

    Quick endpoint to help users decide how to split their time.
    """
    try:
        planner = MultiCityPlanner(db)

        allocation = planner.suggest_days_allocation(
            city_ids=city_ids,
            total_days=total_days
        )

        # Get city names
        from app.db.models import City
        cities = db.query(City).filter(City.id.in_(city_ids)).all()
        city_map = {city.id: city.name for city in cities}

        return {
            "success": True,
            "total_days": total_days,
            "allocation": [
                {
                    "city_id": city_id,
                    "city_name": city_map.get(city_id, "Unknown"),
                    "suggested_days": days
                }
                for city_id, days in allocation.items()
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error suggesting days: {str(e)}")


@router.post("/multi-city/recommend")
async def recommend_city_combinations(
    request: CityRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Recommend complementary cities to visit based on a starting city.

    Helps users discover interesting multi-city combinations.
    """
    try:
        planner = MultiCityPlanner(db)

        recommendations = planner.recommend_city_combinations(
            base_city_id=request.base_city_id,
            num_recommendations=request.num_recommendations,
            interests=request.interests
        )

        return {
            "success": True,
            "base_city_id": request.base_city_id,
            "recommendations": recommendations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recommending cities: {str(e)}")


@router.get("/multi-city/popular-routes")
async def get_popular_routes(db: Session = Depends(get_db)):
    """
    Get popular pre-defined multi-city routes.

    Curated combinations that work well together.
    """
    # Define popular routes
    # These would ideally come from usage data or be curated by travel experts
    popular_routes = [
        {
            "name": "Classic USA West Coast",
            "description": "Experience the best of California",
            "cities": ["San Francisco", "Los Angeles"],
            "suggested_days": 7,
            "highlights": ["Golden Gate Bridge", "Hollywood", "Beaches", "Food scene"]
        },
        {
            "name": "European Grand Tour",
            "description": "Iconic European capitals",
            "cities": ["Paris", "London", "Barcelona", "Rome"],
            "suggested_days": 14,
            "highlights": ["Eiffel Tower", "Colosseum", "Big Ben", "Sagrada Familia"]
        },
        {
            "name": "East Meets West",
            "description": "Cultural fusion experience",
            "cities": ["Tokyo", "Bangkok", "Dubai"],
            "suggested_days": 12,
            "highlights": ["Ancient temples", "Modern skylines", "Street food", "Shopping"]
        },
        {
            "name": "Romance in Europe",
            "description": "Perfect for couples",
            "cities": ["Paris", "Rome", "Barcelona"],
            "suggested_days": 10,
            "highlights": ["Wine & dine", "Art & culture", "Romantic walks", "Architecture"]
        },
        {
            "name": "City Hoppers Special",
            "description": "Urban exploration across continents",
            "cities": ["New York", "London", "Tokyo"],
            "suggested_days": 12,
            "highlights": ["Skyscrapers", "Museums", "Nightlife", "Shopping"]
        }
    ]

    # Enrich with actual city IDs
    from app.db.models import City

    enriched_routes = []
    for route in popular_routes:
        city_names = route["cities"]
        cities = db.query(City).filter(City.name.in_(city_names)).all()

        if len(cities) == len(city_names):
            enriched_routes.append({
                **route,
                "city_ids": [city.id for city in cities],
                "num_cities": len(cities)
            })

    return {
        "success": True,
        "routes": enriched_routes
    }
