"""
Google Places API (New) service for fetching real venues during itinerary refinement.

Used when the user requests a specific type of place (luxury restaurant, rooftop bar, etc.)
and the DB doesn't have a good match. Returns real venues with real coordinates.
"""
import logging
import math
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

# Map our internal categories + user intent keywords to Google Places types
CATEGORY_TO_PLACE_TYPE = {
    "food": "restaurant",
    "nightlife": "bar",
    "culture": "museum",
    "shopping": "shopping_mall",
    "nature": "park",
    "adventure": "tourist_attraction",
    "beaches": "natural_feature",
}

# Keywords that signal the user wants something specific enough to use Google Places
# Also triggers on any category name so "add nightlife" always fetches real venues
REAL_VENUE_TRIGGERS = [
    # Categories
    "food", "nightlife", "culture", "shopping", "nature", "adventure", "beach",
    # Venue types
    "restaurant", "bar", "club", "cafe", "museum", "gallery", "theatre",
    "theater", "spa", "market", "pub", "lounge",
    # Qualifiers
    "luxury", "fine dining", "michelin", "rooftop", "speakeasy", "jazz",
    "specific", "famous", "popular", "best", "top", "authentic", "local",
    "street food", "brunch", "cocktail",
    # Cuisines
    "sushi", "italian", "french", "indian", "chinese", "thai", "mexican",
    # Actions that imply a real place
    "add", "replace", "swap",
]

# Price level mapping for Places API (New)
PRICE_LEVEL_MAP = {
    "PRICE_LEVEL_FREE": (0, "Free"),
    "PRICE_LEVEL_INEXPENSIVE": (1, "Inexpensive"),
    "PRICE_LEVEL_MODERATE": (2, "Moderate"),
    "PRICE_LEVEL_EXPENSIVE": (3, "Expensive"),
    "PRICE_LEVEL_VERY_EXPENSIVE": (4, "Very Expensive"),
}

COST_FROM_PRICE_LEVEL = {0: 5.0, 1: 15.0, 2: 35.0, 3: 75.0, 4: 150.0}


def should_use_places_api(user_message: str, desired_categories: list[str]) -> bool:
    """Decide if we should fetch real venues from Google Places."""
    if not settings.GOOGLE_PLACES_API_KEY:
        return False
    msg = user_message.lower()
    return any(trigger in msg for trigger in REAL_VENUE_TRIGGERS)


async def fetch_real_venues(
    city_lat: float,
    city_lon: float,
    user_message: str,
    desired_categories: list[str],
    max_results: int = 5,
    near_lat: Optional[float] = None,
    near_lon: Optional[float] = None,
    explicit_query: Optional[str] = None,
) -> list[dict]:
    """
    Fetch real venues from Google Places API (New) using Text Search.

    Fetches a larger candidate pool, then re-ranks by a combined score:
        score = rating * log10(review_count + 1) / (distance_km + 0.5)
    so results are popular, highly-rated, and close to the previous activity.

    explicit_query: if provided (from LLM), use directly instead of keyword-guessing.
    near_lat/near_lon: coordinates of the previous activity (for proximity scoring).
    Falls back to city_lat/city_lon if not provided.

    Returns list of dicts with: name, rating, address, lat, lon, place_id, price_level, price_label
    """
    if not settings.GOOGLE_PLACES_API_KEY:
        return []

    # Use previous activity location for proximity if available
    ref_lat = near_lat if near_lat is not None else city_lat
    ref_lon = near_lon if near_lon is not None else city_lon

    # LLM-provided query takes precedence over keyword guessing
    keyword = explicit_query if explicit_query else _build_search_keyword(user_message, desired_categories)
    radius = 8000  # 8km from city center

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": (
            "places.displayName,places.rating,places.formattedAddress,"
            "places.location,places.id,places.types,places.priceLevel,places.userRatingCount"
        ),
    }
    body = {
        "textQuery": keyword,
        "maxResultCount": 15,  # Fetch more so we can re-rank
        "locationBias": {
            "circle": {
                "center": {"latitude": city_lat, "longitude": city_lon},
                "radius": float(radius),
            }
        },
        "rankPreference": "RELEVANCE",
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(url, headers=headers, json=body)
            data = response.json()

        if response.status_code != 200:
            logger.warning(
                f"Places API (New) error {response.status_code}: "
                f"{data.get('error', {}).get('message', str(data))}"
            )
            return []

        raw_places = data.get("places", [])
        venues = []

        for place in raw_places:
            location = place.get("location", {})
            price_level_str = place.get("priceLevel", "")
            price_num, price_label = PRICE_LEVEL_MAP.get(price_level_str, (None, ""))
            rating = float(place.get("rating", 0.0))
            review_count = int(place.get("userRatingCount", 0))

            # Skip venues with no rating or very few reviews
            if rating == 0.0 or review_count < 10:
                continue

            lat = location.get("latitude", city_lat)
            lon = location.get("longitude", city_lon)
            distance_km = _haversine_km(ref_lat, ref_lon, lat, lon)

            # Combined score: high rating + many reviews + close proximity
            popularity_score = rating * math.log10(review_count + 1)
            proximity_score = popularity_score / (distance_km + 0.5)

            venue = {
                "name": place.get("displayName", {}).get("text", "Unknown"),
                "rating": rating,
                "address": place.get("formattedAddress", ""),
                "latitude": lat,
                "longitude": lon,
                "place_id": place.get("id", ""),
                "types": place.get("types", []),
                "price_level": price_num,
                "price_label": price_label,
                "user_ratings_total": review_count,
                "_score": proximity_score,
            }
            venues.append(venue)

        # Sort by combined score descending
        venues.sort(key=lambda v: v["_score"], reverse=True)
        for v in venues:
            v.pop("_score")

        venues = venues[:max_results]
        logger.info(f"Google Places (New) returned {len(venues)} venues for '{keyword}' (re-ranked by rating+popularity+proximity)")
        return venues

    except Exception as e:
        logger.error(f"Google Places API call failed: {e}")
        return []


def venues_to_activity_like(venues: list[dict], category: str, avg_duration_minutes: int = 90) -> list[dict]:
    """
    Convert Google Places venues to activity-like dicts for slot-filling and display.
    These are NOT DB activities — they're real-world venues.
    """
    activities = []
    for v in venues:
        price_level = v.get("price_level")
        estimated_cost = COST_FROM_PRICE_LEVEL.get(price_level, 25.0) if price_level is not None else 25.0

        activities.append({
            "name": v["name"],
            "category": category,
            "cost": estimated_cost,
            "duration": avg_duration_minutes,
            "rating": v["rating"],
            "latitude": v["latitude"],
            "longitude": v["longitude"],
            "address": v["address"],
            "place_id": v["place_id"],
            "price_label": v.get("price_label", ""),
            "total_reviews": v.get("user_ratings_total", 0),
            "source": "google_places",
        })

    return activities


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in km between two coordinates."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


CATEGORY_SEARCH_TERMS = {
    "nightlife": "bar nightclub lounge",
    "food": "restaurant",
    "culture": "museum art gallery",
    "shopping": "shopping mall market",
    "nature": "park garden nature",
    "adventure": "adventure outdoor activity",
    "beaches": "beach",
}


def _build_search_keyword(user_message: str, desired_categories: list[str]) -> str:
    """Build a Google Places text search query from user message and categories."""
    msg = user_message.lower()

    # Category always wins if we have a clear desired category
    if desired_categories:
        cat = desired_categories[0]
        # Apply qualifiers on top of the category
        if any(w in msg for w in ["luxury", "fine dining", "michelin", "upscale", "high-end"]):
            return f"luxury fine dining {CATEGORY_SEARCH_TERMS.get(cat, cat)}"
        if "rooftop" in msg and cat == "nightlife":
            return "rooftop bar"
        if any(w in msg for w in ["street food", "local food", "authentic"]) and cat == "food":
            return "authentic local street food"
        if "jazz" in msg and cat == "nightlife":
            return "jazz bar live music"
        if any(w in msg for w in ["cocktail", "speakeasy"]) and cat == "nightlife":
            return "cocktail speakeasy bar"
        if "brunch" in msg and cat == "food":
            return "brunch restaurant"
        if any(w in msg for w in ["sushi", "japanese"]) and cat == "food":
            return "sushi restaurant"
        if any(w in msg for w in ["italian", "pizza", "pasta"]) and cat == "food":
            return "italian restaurant"
        if "indian" in msg and cat == "food":
            return "indian restaurant"
        if "spa" in msg:
            return "luxury spa wellness"
        # Default: use category search terms
        return CATEGORY_SEARCH_TERMS.get(cat, cat)

    # No category — parse from message
    if any(w in msg for w in ["luxury", "fine dining", "michelin"]):
        return "luxury fine dining restaurant"
    if "rooftop" in msg:
        return "rooftop bar restaurant"
    if "jazz" in msg:
        return "jazz bar live music"
    if "spa" in msg:
        return "luxury spa wellness"

    return msg[:60]
