"""OR-Tools based optimizer for advanced itinerary planning."""
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Tuple
from ortools.sat.python import cp_model
from app.api.schemas import (
    TripPreferences,
    ItineraryDay,
    ItineraryBlock,
    ItinerarySummary,
    ActivitySummary,
    Coordinates,
    EnergyLevel,
)
from app.db.models import Activity
from app.core.scoring import (
    score_activity,
    haversine_distance,
    estimate_travel_time,
    get_budget_threshold,
)
from app.core.optimizer import (
    Itinerary,
    get_activities_per_day,
    get_day_start_time,
    is_activity_available,
)


def build_itinerary_ortools(
    preferences: TripPreferences, activities: List[Activity]
) -> Itinerary:
    """
    Build an optimized itinerary using OR-Tools CP-SAT solver.
    
    This is a more advanced optimizer that uses constraint programming
    to find optimal solutions considering multiple objectives.
    """
    itinerary = Itinerary()
    
    # Calculate trip duration
    trip_days = (preferences.end_date - preferences.start_date).days + 1
    min_activities, max_activities = get_activities_per_day(
        preferences.energy_level
    )
    
    if not activities:
        return itinerary
    
    # For now, use greedy as fallback for complex cases
    # OR-Tools implementation for full optimization would be very complex
    # This is a simplified version that demonstrates the approach
    
    # Filter activities based on constraints
    available_activities = []
    must_visit_names = set()
    if preferences.constraints and preferences.constraints.must_visit:
        must_visit_names = set(preferences.constraints.must_visit)
    
    for activity in activities:
        # Skip if in avoid list
        if (
            preferences.constraints
            and preferences.constraints.avoid
            and activity.name in preferences.constraints.avoid
        ):
            continue
        available_activities.append(activity)
    
    # If we have must-visit activities, ensure they're included
    must_visit_activities = [
        a for a in available_activities if a.name in must_visit_names
    ]
    
    # For v2, we'll use a hybrid approach:
    # 1. Use OR-Tools for day-level optimization (which activities per day)
    # 2. Use greedy for ordering within each day (simpler and faster)
    
    # Create model
    model = cp_model.CpModel()
    
    # Decision variables: activity_selected[day][activity_idx] = 1 if activity is selected for that day
    activity_selected = {}
    for day in range(trip_days):
        for act_idx, activity in enumerate(available_activities):
            activity_selected[(day, act_idx)] = model.NewBoolVar(
                f"activity_{day}_{act_idx}"
            )
    
    # Constraints
    daily_budget = get_budget_threshold(
        preferences.budget_level.value, preferences.budget_per_day
    )

    # Scale budget to cents (integers) for OR-Tools CP-SAT solver
    daily_budget_cents = int(daily_budget * 100)

    # 1. Budget constraint per day (using cents to avoid floats)
    for day in range(trip_days):
        daily_cost = sum(
            activity_selected[(day, act_idx)] * int(available_activities[act_idx].base_cost * 100)
            for act_idx in range(len(available_activities))
        )
        model.Add(daily_cost <= int(daily_budget_cents * 1.2))  # Allow 20% flexibility
    
    # 2. Activity count per day (based on energy level)
    for day in range(trip_days):
        daily_count = sum(
            activity_selected[(day, act_idx)]
            for act_idx in range(len(available_activities))
        )
        model.Add(daily_count >= min_activities)
        model.Add(daily_count <= max_activities)
    
    # 3. Must-visit activities must be included somewhere
    for must_visit_name in must_visit_names:
        must_visit_indices = [
            act_idx
            for act_idx, act in enumerate(available_activities)
            if act.name == must_visit_name
        ]
        if must_visit_indices:
            # At least one day must include this activity
            model.Add(
                sum(
                    activity_selected[(day, act_idx)]
                    for day in range(trip_days)
                    for act_idx in must_visit_indices
                ) >= 1
            )
    
    # 4. No duplicate activities in same day (unless must-visit)
    for day in range(trip_days):
        for act_idx in range(len(available_activities)):
            # Can only select once per day
            model.Add(activity_selected[(day, act_idx)] <= 1)
    
    # Objective: Maximize total utility score
    # Utility = sum of activity scores weighted by rating, category match, etc.
    total_utility = []
    for day in range(trip_days):
        current_date = preferences.start_date + timedelta(days=day)
        day_start = get_day_start_time().replace(
            year=current_date.year,
            month=current_date.month,
            day=current_date.day,
        )
        
        day_state = {
            "current_cost": 0.0,
            "available_time_minutes": 480,  # 8 hours
        }
        
        for act_idx, activity in enumerate(available_activities):
            # Calculate base score for this activity
            score = score_activity(activity, preferences, day_state, None)
            # Weight by selection (ensure integer for OR-Tools)
            score_int = int(round(score * 100))
            total_utility.append(
                activity_selected[(day, act_idx)] * score_int  # Scale for integer solver
            )
    
    model.Maximize(sum(total_utility))
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0  # Limit solve time
    status = solver.Solve(model)
    
    # If solution found, build itinerary
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # Build days from solution
        for day in range(trip_days):
            current_date = preferences.start_date + timedelta(days=day)
            day_start = get_day_start_time().replace(
                year=current_date.year,
                month=current_date.month,
                day=current_date.day,
            )
            
            # Get selected activities for this day
            selected_activities = [
                available_activities[act_idx]
                for act_idx in range(len(available_activities))
                if solver.Value(activity_selected[(day, act_idx)]) == 1
            ]
            
            if not selected_activities:
                continue
            
            # Order activities using greedy (simpler than full TSP)
            blocks = []
            current_time = day_start
            daily_cost = 0.0
            daily_duration = 0
            previous_activity: Optional[Activity] = None
            used_in_day = set()
            
            while selected_activities and len(blocks) < max_activities:
                day_end = day_start.replace(hour=22, minute=0)
                available_time = (day_end - current_time).total_seconds() / 60
                
                if available_time < 30:
                    break
                
                # Find best next activity
                best_activity = None
                best_score = -1
                best_travel_time = 0
                
                day_state = {
                    "current_cost": daily_cost,
                    "available_time_minutes": int(available_time),
                }
                
                for activity in selected_activities:
                    if activity.id in used_in_day:
                        continue
                    
                    if not is_activity_available(activity, current_time):
                        continue
                    
                    travel_time = 0
                    if previous_activity:
                        distance = haversine_distance(
                            previous_activity.latitude,
                            previous_activity.longitude,
                            activity.latitude,
                            activity.longitude,
                        )
                        travel_time = estimate_travel_time(
                            distance, preferences.travel_mode
                        )
                    
                    total_time_needed = travel_time + activity.avg_duration_minutes
                    if total_time_needed > available_time:
                        continue
                    
                    score = score_activity(
                        activity, preferences, day_state, previous_activity
                    )
                    
                    if score > best_score:
                        best_score = score
                        best_activity = activity
                        best_travel_time = travel_time
                
                if best_activity is None:
                    break
                
                # Add activity
                current_time += timedelta(minutes=best_travel_time)
                start_time = current_time
                end_time = start_time + timedelta(
                    minutes=best_activity.avg_duration_minutes
                )
                
                activity_summary = ActivitySummary(
                    id=best_activity.id,
                    name=best_activity.name,
                    category=best_activity.category,
                    cost=best_activity.base_cost,
                    duration=best_activity.avg_duration_minutes,
                    rating=best_activity.rating,
                    coordinates=Coordinates(
                        latitude=best_activity.latitude,
                        longitude=best_activity.longitude,
                    ),
                    tags=best_activity.tags if hasattr(best_activity, 'tags') else None,
                    description=best_activity.description if hasattr(best_activity, 'description') else None,
                )
                
                block = ItineraryBlock(
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat(),
                    activity=activity_summary,
                    travel_time_from_previous=best_travel_time if best_travel_time > 0 else None,
                )
                
                blocks.append(block)
                current_time = end_time
                daily_cost += best_activity.base_cost
                daily_duration += best_activity.avg_duration_minutes + best_travel_time
                previous_activity = best_activity
                used_in_day.add(best_activity.id)
                selected_activities.remove(best_activity)
            
            if blocks:
                day_obj = ItineraryDay(
                    date=current_date,
                    total_cost=daily_cost,
                    total_duration_minutes=daily_duration,
                    blocks=blocks,
                )
                itinerary.days.append(day_obj)
    
    # Calculate summary (same as greedy optimizer)
    if itinerary.days:
        total_cost = sum(day.total_cost for day in itinerary.days)
        avg_cost_per_day = total_cost / len(itinerary.days)
        
        categories_covered = set()
        for day in itinerary.days:
            for block in day.blocks:
                categories_covered.add(block.activity.category)
        
        avg_activities_per_day = sum(
            len(day.blocks) for day in itinerary.days
        ) / len(itinerary.days)
        if avg_activities_per_day <= 3:
            pace_label = "Relaxed"
        elif avg_activities_per_day <= 5:
            pace_label = "Moderate"
        else:
            pace_label = "Active"
        
        itinerary.summary = ItinerarySummary(
            total_cost=total_cost,
            avg_cost_per_day=avg_cost_per_day,
            categories_covered=sorted(list(categories_covered)),
            pace_label=pace_label,
        )
        
        # Calculate scores
        budget_utilization = min(1.0, total_cost / (daily_budget * len(itinerary.days)))
        category_coverage = len(categories_covered) / max(1, len(preferences.preferred_categories) if preferences.preferred_categories else 7)
        avg_rating = sum(
            block.activity.rating
            for day in itinerary.days
            for block in day.blocks
        ) / max(1, sum(len(day.blocks) for day in itinerary.days))
        rating_score = avg_rating / 5.0
        
        itinerary.optimization_score = (
            budget_utilization * 0.3 + category_coverage * 0.4 + rating_score * 0.3
        )
        
        confidence = 0.7
        if preferences.preferred_categories:
            matched_categories = len(
                set(categories_covered) & set(cat.value for cat in preferences.preferred_categories)
            )
            confidence += (matched_categories / len(preferences.preferred_categories)) * 0.3
        itinerary.confidence_score = min(1.0, confidence)
    else:
        itinerary.summary = ItinerarySummary(
            total_cost=0.0,
            avg_cost_per_day=0.0,
            categories_covered=[],
            pace_label="None",
        )
        itinerary.optimization_score = 0.0
        itinerary.confidence_score = 0.0
    
    return itinerary

