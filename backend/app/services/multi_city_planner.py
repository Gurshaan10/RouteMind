"""Multi-city trip planner service."""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.db.models import City, Activity
from app.core.optimizer import build_itinerary
from app.api.schemas import TripPreferences
from datetime import datetime, timedelta
import math


class MultiCityPlanner:
    """
    Plans itineraries across multiple cities.

    Features:
    - Suggests optimal days allocation per city
    - Creates separate itineraries for each city
    - Provides cohesive multi-city trip plan
    - Recommends city combinations based on preferences
    """

    def __init__(self, db: Session):
        self.db = db

    def suggest_days_allocation(
        self,
        city_ids: List[int],
        total_days: int,
        budget_per_day: Optional[float] = None
    ) -> Dict[int, int]:
        """
        Suggest how many days to spend in each city.

        Allocation strategy:
        - Larger cities with more activities get more days
        - Minimum 2 days per city
        - Distribute remaining days based on activity count

        Args:
            city_ids: List of city IDs to visit
            total_days: Total trip duration in days
            budget_per_day: Optional budget constraint per day

        Returns:
            Dict mapping city_id -> number_of_days
        """
        if not city_ids:
            return {}

        # Get activity counts for each city
        city_activity_counts = {}
        for city_id in city_ids:
            count = self.db.query(Activity).filter(Activity.city_id == city_id).count()
            city_activity_counts[city_id] = max(count, 1)  # At least 1 to avoid division by zero

        # Calculate base allocation (minimum 2 days per city)
        min_days_per_city = 2
        num_cities = len(city_ids)
        base_days_needed = min_days_per_city * num_cities

        if total_days < base_days_needed:
            # Not enough days, allocate evenly
            days_per_city = total_days // num_cities
            remainder = total_days % num_cities

            allocation = {}
            sorted_cities = sorted(city_ids, key=lambda c: city_activity_counts[c], reverse=True)

            for i, city_id in enumerate(sorted_cities):
                allocation[city_id] = days_per_city + (1 if i < remainder else 0)

            return allocation

        # We have enough days, allocate based on activity counts
        remaining_days = total_days - base_days_needed
        total_activities = sum(city_activity_counts.values())

        allocation = {}
        for city_id in city_ids:
            # Base allocation
            base = min_days_per_city

            # Additional days proportional to activity count
            activity_ratio = city_activity_counts[city_id] / total_activities
            additional = math.floor(remaining_days * activity_ratio)

            allocation[city_id] = base + additional

        # Distribute any leftover days to cities with most activities
        allocated_total = sum(allocation.values())
        leftover = total_days - allocated_total

        if leftover > 0:
            sorted_cities = sorted(city_ids, key=lambda c: city_activity_counts[c], reverse=True)
            for i in range(leftover):
                allocation[sorted_cities[i % len(sorted_cities)]] += 1

        return allocation

    def plan_multi_city_trip(
        self,
        city_ids: List[int],
        total_days: int,
        budget: Optional[float] = None,
        interests: Optional[List[str]] = None,
        pace: str = "moderate"
    ) -> Dict:
        """
        Create a complete multi-city trip plan.

        Args:
            city_ids: List of city IDs to visit
            total_days: Total trip duration
            budget: Total budget for the trip
            interests: List of interest categories (food, culture, nature, etc.)
            pace: Trip pace (relaxed, moderate, packed)

        Returns:
            Complete multi-city trip plan with itineraries for each city
        """
        if not city_ids:
            return {
                "error": "No cities provided",
                "cities": [],
                "total_days": 0,
                "total_cost": 0
            }

        # Get cities
        cities = self.db.query(City).filter(City.id.in_(city_ids)).all()
        city_map = {city.id: city for city in cities}

        # Suggest days allocation
        days_allocation = self.suggest_days_allocation(city_ids, total_days, budget)

        # Calculate budget per city if total budget provided
        budget_per_city = {}
        if budget:
            total_allocated_days = sum(days_allocation.values())
            for city_id, days in days_allocation.items():
                budget_per_city[city_id] = (budget * days) / total_allocated_days

        # Create itinerary for each city
        city_itineraries = []
        total_cost = 0
        current_date = datetime.now()

        for city_id in city_ids:
            if city_id not in city_map:
                continue

            city = city_map[city_id]
            days_in_city = days_allocation[city_id]
            city_budget = budget_per_city.get(city_id)

            # Calculate date range for this city
            start_date = current_date
            end_date = current_date + timedelta(days=days_in_city - 1)

            # Map pace to energy_level
            energy_map = {"relaxed": "relaxed", "moderate": "moderate", "packed": "active"}
            energy_level = energy_map.get(pace, "moderate")

            # Determine budget_level from budget_per_day
            budget_per_day = city_budget / days_in_city if city_budget else None
            if budget_per_day:
                if budget_per_day < 50:
                    budget_level = "low"
                elif budget_per_day < 150:
                    budget_level = "medium"
                else:
                    budget_level = "high"
            else:
                budget_level = "medium"

            # Determine trip_type based on days
            if days_in_city == 1:
                trip_type = "day_trip"
            elif days_in_city <= 3:
                trip_type = "weekend"
            elif days_in_city <= 7:
                trip_type = "one_week"
            else:
                trip_type = "long"

            # Create trip preferences for this city
            preferences = TripPreferences(
                destination_city_id=city_id,
                start_date=start_date.date(),
                end_date=end_date.date(),
                trip_type=trip_type,
                budget_level=budget_level,
                budget_per_day=budget_per_day,
                preferred_categories=interests or [],
                energy_level=energy_level,
                travel_mode="mixed"
            )

            # Plan itinerary for this city
            try:
                # Get activities for this city
                activities = self.db.query(Activity).filter(Activity.city_id == city_id).all()

                if not activities:
                    city_itineraries.append({
                        "city_id": city_id,
                        "city_name": city.name,
                        "country": city.country,
                        "days_allocated": days_in_city,
                        "error": "No activities found for this city"
                    })
                    continue

                # Build itinerary using core optimizer
                itinerary = build_itinerary(preferences, activities, use_ortools=False)

                # Calculate total cost from itinerary days
                city_total_cost = sum(day.total_cost for day in itinerary.days)

                city_itineraries.append({
                    "city_id": city_id,
                    "city_name": city.name,
                    "country": city.country,
                    "days_allocated": days_in_city,
                    "start_date": current_date.strftime("%Y-%m-%d"),
                    "end_date": (current_date + timedelta(days=days_in_city - 1)).strftime("%Y-%m-%d"),
                    "itinerary": {
                        "days": [
                            {
                                "date": day.date,
                                "total_cost": day.total_cost,
                                "total_duration_minutes": day.total_duration_minutes,
                                "blocks": [
                                    {
                                        "start_time": block.start_time,
                                        "end_time": block.end_time,
                                        "activity": {
                                            "id": block.activity.id,
                                            "name": block.activity.name,
                                            "category": block.activity.category,
                                            "cost": block.activity.cost,
                                            "duration": block.activity.duration,
                                            "rating": block.activity.rating,
                                            "coordinates": {
                                                "latitude": block.activity.coordinates.latitude,
                                                "longitude": block.activity.coordinates.longitude
                                            }
                                        },
                                        "travel_time_from_previous": block.travel_time_from_previous
                                    } for block in day.blocks
                                ]
                            } for day in itinerary.days
                        ],
                        "summary": {
                            "total_cost": itinerary.summary.total_cost,
                            "categories_covered": itinerary.summary.categories_covered
                        }
                    },
                    "budget_allocated": city_budget,
                    "estimated_cost": city_total_cost,
                    # Store raw itinerary + preferences so the endpoint can generate narrative
                    "_itinerary_obj": itinerary,
                    "_preferences_obj": preferences,
                })

                total_cost += city_total_cost
                current_date += timedelta(days=days_in_city)

            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error planning itinerary for {city.name}: {e}")
                city_itineraries.append({
                    "city_id": city_id,
                    "city_name": city.name,
                    "country": city.country,
                    "days_allocated": days_in_city,
                    "error": str(e)
                })

        return {
            "total_cities": len(city_ids),
            "total_days": total_days,
            "total_budget": budget,
            "total_estimated_cost": total_cost,
            "budget_remaining": (budget - total_cost) if budget else None,
            "cities": city_itineraries,
            "trip_start": city_itineraries[0]["start_date"] if city_itineraries else None,
            "trip_end": city_itineraries[-1]["end_date"] if city_itineraries else None,
            "pace": pace,
            "interests": interests or []
        }

    def recommend_city_combinations(
        self,
        base_city_id: int,
        num_recommendations: int = 3,
        interests: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Recommend city combinations based on a starting city.

        Strategy:
        - Suggest cities with complementary activities
        - Consider geographical diversity
        - Match user interests

        Args:
            base_city_id: Starting city ID
            num_recommendations: Number of combinations to return
            interests: User's interest categories

        Returns:
            List of recommended city combinations
        """
        base_city = self.db.query(City).filter(City.id == base_city_id).first()
        if not base_city:
            return []

        # Get all other cities
        other_cities = self.db.query(City).filter(City.id != base_city_id).all()

        # Score each city based on complementarity
        city_scores = []
        for city in other_cities:
            score = self._score_city_combination(base_city, city, interests)
            city_scores.append({
                "city": city,
                "score": score
            })

        # Sort by score and take top recommendations
        city_scores.sort(key=lambda x: x["score"], reverse=True)

        recommendations = []
        for item in city_scores[:num_recommendations]:
            city = item["city"]

            # Get activity stats
            activities = self.db.query(Activity).filter(Activity.city_id == city.id).all()
            category_counts = {}
            for activity in activities:
                category_counts[activity.category] = category_counts.get(activity.category, 0) + 1

            recommendations.append({
                "city_id": city.id,
                "city_name": city.name,
                "country": city.country,
                "score": item["score"],
                "total_activities": len(activities),
                "top_categories": sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3],
                "reason": self._get_recommendation_reason(base_city, city, interests)
            })

        return recommendations

    def _score_city_combination(
        self,
        base_city: City,
        candidate_city: City,
        interests: Optional[List[str]] = None
    ) -> float:
        """Score how well a candidate city complements the base city."""
        score = 0.0

        # Different country = cultural diversity bonus
        if base_city.country != candidate_city.country:
            score += 30

        # Get activities for both cities
        base_activities = self.db.query(Activity).filter(Activity.city_id == base_city.id).all()
        candidate_activities = self.db.query(Activity).filter(Activity.city_id == candidate_city.id).all()

        # Category diversity score
        base_categories = set(a.category for a in base_activities)
        candidate_categories = set(a.category for a in candidate_activities)

        # Unique categories in candidate = good
        unique_categories = candidate_categories - base_categories
        score += len(unique_categories) * 10

        # Matching interests bonus
        if interests:
            matching_categories = candidate_categories.intersection(set(interests))
            score += len(matching_categories) * 15

        # High-rated activities bonus
        high_rated = sum(1 for a in candidate_activities if a.rating >= 4.5)
        score += high_rated * 2

        # Activity count (more options = better)
        score += min(len(candidate_activities) / 5, 20)  # Cap at 20 points

        return score

    def _get_recommendation_reason(
        self,
        base_city: City,
        recommended_city: City,
        interests: Optional[List[str]] = None
    ) -> str:
        """Generate a human-readable reason for the recommendation."""
        reasons = []

        if base_city.country != recommended_city.country:
            reasons.append(f"Experience {recommended_city.country}'s culture")

        # Get top categories
        activities = self.db.query(Activity).filter(Activity.city_id == recommended_city.id).all()
        category_counts = {}
        for activity in activities:
            category_counts[activity.category] = category_counts.get(activity.category, 0) + 1

        if category_counts:
            top_category = max(category_counts.items(), key=lambda x: x[1])[0]
            reasons.append(f"Great for {top_category}")

        if interests and set(interests).intersection(set(category_counts.keys())):
            reasons.append("Matches your interests")

        high_rated_count = sum(1 for a in activities if a.rating >= 4.5)
        if high_rated_count >= 5:
            reasons.append(f"{high_rated_count} highly-rated attractions")

        return ", ".join(reasons) if reasons else "Great destination choice"


