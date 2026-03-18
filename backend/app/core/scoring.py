"""Scoring engine for activities based on user preferences."""
import math
from typing import Optional, Tuple
from app.api.schemas import TripPreferences, Category, TravelMode, SelectionExplanation
from app.db.models import Activity


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula (in km)."""
    R = 6371  # Earth radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def estimate_travel_time(
    distance_km: float, travel_mode: TravelMode
) -> int:
    """Estimate travel time in minutes based on distance and travel mode."""
    # Average speeds in km/h
    speeds = {
        TravelMode.walking: 5.0,
        TravelMode.public_transport: 25.0,  # Including wait time
        TravelMode.taxi: 30.0,
        TravelMode.self_drive: 40.0,
        TravelMode.mixed: 20.0,  # Average of walking and transport
    }
    
    speed = speeds.get(travel_mode, 20.0)
    time_hours = distance_km / speed
    return int(time_hours * 60)  # Convert to minutes


def get_budget_threshold(budget_level: str, budget_per_day: Optional[float]) -> float:
    """Get numeric budget threshold based on budget level."""
    if budget_per_day is not None:
        return budget_per_day
    
    thresholds = {
        "low": 50.0,
        "medium": 150.0,
        "high": 300.0,
    }
    return thresholds.get(budget_level, 150.0)


def score_activity(
    activity: Activity,
    preferences: TripPreferences,
    day_state: dict,
    previous_activity: Optional[Activity] = None,
    explain: bool = False,
    semantic_relevance_score: Optional[float] = None,
) -> float | Tuple[float, SelectionExplanation]:
    """
    Score an activity based on user preferences and current day state.

    Returns a score from 0-100, higher is better.
    If explain=True, returns (score, SelectionExplanation).
    """
    score = 0.0

    # 1. Rating component (0-40 points)
    rating_score = (activity.rating / 5.0) * 40.0
    score += rating_score

    if activity.rating >= 4.5:
        rating_quality = "excellent (4.5+)"
    elif activity.rating >= 3.5:
        rating_quality = "good (3.5+)"
    elif activity.rating >= 2.5:
        rating_quality = "average"
    else:
        rating_quality = "below average"

    # 2. Category match (0-30 points)
    category_match = False
    if preferences.preferred_categories:
        if activity.category in [cat.value for cat in preferences.preferred_categories]:
            score += 30.0
            category_match = True
        else:
            score += 5.0
    else:
        score += 15.0

    # 3. Cost component (0-20 points)
    daily_budget = get_budget_threshold(
        preferences.budget_level.value, preferences.budget_per_day
    )
    current_daily_cost = day_state.get("current_cost", 0.0)
    projected_cost = current_daily_cost + activity.base_cost

    if projected_cost <= daily_budget:
        score += 20.0
        budget_fit = "within budget"
    elif projected_cost <= daily_budget * 1.2:
        score += 10.0
        budget_fit = "slightly over"
    else:
        score += max(0.0, 20.0 - (projected_cost - daily_budget) / 10.0)
        budget_fit = "over budget"

    # 4. Duration fit (0-10 points)
    available_time = day_state.get("available_time_minutes", 480)
    if activity.avg_duration_minutes <= available_time:
        score += 10.0
        time_fit = "fits perfectly"
    else:
        score += max(0.0, 10.0 - (activity.avg_duration_minutes - available_time) / 30.0)
        time_fit = "tight fit" if activity.avg_duration_minutes <= available_time * 1.2 else "too long"

    # 5. Distance penalty — strong enough to enforce geographic ordering
    travel_time = 0
    travel_proximity = "first activity"
    if previous_activity:
        distance = haversine_distance(
            previous_activity.latitude,
            previous_activity.longitude,
            activity.latitude,
            activity.longitude,
        )
        travel_time = estimate_travel_time(distance, preferences.travel_mode)

        # Strong proximity penalty: 2pts per minute of travel, uncapped
        # A 30min trip costs 60pts — more than the entire rating component (40pts max)
        # This enforces geographic clustering and prevents cross-city zigzags
        travel_penalty = travel_time * 2.0
        score -= travel_penalty

        if travel_time > 45:
            travel_proximity = "far (>30min)"
        elif travel_time > 20:
            travel_proximity = "moderate (15-30min)"
        else:
            travel_proximity = "nearby (<15min)"

    # 6. Constraints check
    is_must_visit = False
    if preferences.constraints:
        if (
            preferences.constraints.must_visit
            and activity.name in preferences.constraints.must_visit
        ):
            score += 50.0
            is_must_visit = True

        if (
            preferences.constraints.avoid
            and activity.name in preferences.constraints.avoid
        ):
            score = -100.0

    final_score = max(0.0, score)

    if not explain:
        return final_score

    # Build human-readable summary
    reasons = []
    if is_must_visit:
        reasons.append("must-visit destination")
    if category_match:
        reasons.append(f"matches your {activity.category} preference")
    if semantic_relevance_score is not None and semantic_relevance_score > 0.7:
        reasons.append("highly relevant to your trip style")
    if budget_fit == "within budget":
        reasons.append("fits your budget")
    if travel_proximity == "nearby (<15min)":
        reasons.append("conveniently close")
    if rating_quality in ("excellent (4.5+)", "good (3.5+)"):
        reasons.append(f"{rating_quality} rating")

    summary = (
        f"Chosen for its {', '.join(reasons)}." if reasons
        else f"Best available option given your preferences."
    )

    explanation = SelectionExplanation(
        category_match=category_match,
        semantic_relevance_score=semantic_relevance_score,
        budget_fit=budget_fit,
        time_fit=time_fit,
        travel_proximity=travel_proximity,
        rating_quality=rating_quality,
        must_visit=is_must_visit,
        summary=summary,
    )

    return final_score, explanation

