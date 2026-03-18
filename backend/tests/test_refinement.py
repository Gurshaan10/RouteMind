"""
Tests for the refinement service — deterministic logic only (no LLM calls).

These tests cover:
- _format_itinerary_compact
- _apply_remove
- _apply_replace
- _apply_add
- _resolve_candidates
- _pick_best_candidate
- _is_global_restructure
- _apply_global_trim
- _graceful_error
"""
import pytest
from datetime import date, time

from app.api.schemas import (
    TripPreferences,
    BudgetLevel,
    EnergyLevel,
    TravelMode,
    Category,
    ItineraryResponse,
    ItineraryDay,
    ItineraryBlock,
    ActivitySummary,
    Coordinates,
    RefinementIntent,
    ItinerarySummary,
    NarrativeResult,
)
from app.db.models import Activity
from app.services.refinement_service import (
    _format_itinerary_compact,
    _apply_remove,
    _apply_replace,
    _apply_add,
    _resolve_candidates,
    _pick_best_candidate,
    _is_global_restructure,
    _apply_global_trim,
    _graceful_error,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_preferences():
    return TripPreferences(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 2),
        destination_city_id=1,
        trip_type="weekend",
        budget_level=BudgetLevel.medium,
        preferred_categories=[Category.culture, Category.food],
        energy_level=EnergyLevel.moderate,
        travel_mode=TravelMode.mixed,
    )


def _make_activity(id, name, category="culture", cost=30.0, duration=90, rating=4.0,
                   lat=37.77, lon=-122.41):
    return Activity(
        id=id, city_id=1, name=name, category=category,
        base_cost=cost, avg_duration_minutes=duration,
        rating=rating, latitude=lat, longitude=lon,
    )


def _make_block(name, category="culture", cost=30.0, duration=90, rating=4.0,
                start="2024-06-01T09:00:00", end="2024-06-01T10:30:00"):
    return ItineraryBlock(
        start_time=start,
        end_time=end,
        activity=ActivitySummary(
            id=1, name=name, category=category, cost=cost,
            duration=duration, rating=rating,
            coordinates=Coordinates(latitude=37.77, longitude=-122.41),
        ),
        travel_time_from_previous=None,
    )


def _make_itinerary(blocks_day1=None, blocks_day2=None):
    blocks_day1 = blocks_day1 or [_make_block("Museum", start="2024-06-01T09:00:00", end="2024-06-01T10:30:00")]
    days = [
        ItineraryDay(
            date="2024-06-01",
            blocks=blocks_day1,
            total_cost=30.0,
            total_duration_minutes=90,
        )
    ]
    if blocks_day2 is not None:
        days.append(ItineraryDay(
            date="2024-06-02",
            blocks=blocks_day2,
            total_cost=30.0,
            total_duration_minutes=90,
        ))
    return ItineraryResponse(
        days=days,
        summary=ItinerarySummary(
            total_cost=30.0,
            avg_cost_per_day=30.0,
            categories_covered=["culture"],
            pace_label="Moderate",
        ),
        optimization_score=0.8,
        confidence_score=0.9,
        narrative=NarrativeResult(narrative_text="Test narrative"),
    )


# ─── _format_itinerary_compact ───────────────────────────────────────────────

def test_format_itinerary_compact_output():
    itinerary = _make_itinerary()
    text = _format_itinerary_compact(itinerary)
    assert "Day 1" in text
    assert "Museum" in text
    assert "culture" in text


def test_format_itinerary_compact_multi_day():
    itinerary = _make_itinerary(
        blocks_day1=[_make_block("Museum")],
        blocks_day2=[_make_block("Park", category="nature")],
    )
    text = _format_itinerary_compact(itinerary)
    assert "Day 1" in text
    assert "Day 2" in text
    assert "Park" in text


# ─── _apply_remove ───────────────────────────────────────────────────────────

def test_apply_remove_existing_activity():
    blocks = [_make_block("Museum"), _make_block("Park", category="nature",
              start="2024-06-01T11:00:00", end="2024-06-01T12:30:00")]
    day = ItineraryDay(date="2024-06-01", blocks=blocks, total_cost=60.0, total_duration_minutes=180)
    intent = RefinementIntent(
        action="remove", target_day=1, target_activity_name="Museum",
        desired_categories=[], avoid_categories=[], replacement_candidates=[],
        venue_search_query=None, explanation="",
    )
    result_day, change = _apply_remove(day, intent)
    assert change is not None
    assert len(result_day.blocks) == 1
    assert result_day.blocks[0].activity.name == "Park"


def test_apply_remove_nonexistent_activity():
    blocks = [_make_block("Museum")]
    day = ItineraryDay(date="2024-06-01", blocks=blocks, total_cost=30.0, total_duration_minutes=90)
    intent = RefinementIntent(
        action="remove", target_day=1, target_activity_name="Beach",
        desired_categories=[], avoid_categories=[], replacement_candidates=[],
        venue_search_query=None, explanation="",
    )
    result_day, change = _apply_remove(day, intent)
    assert change is None
    assert len(result_day.blocks) == 1  # Unchanged


# ─── _apply_replace ──────────────────────────────────────────────────────────

def test_apply_replace_swaps_activity(sample_preferences):
    block = _make_block("Museum")
    day = ItineraryDay(date="2024-06-01", blocks=[block], total_cost=30.0, total_duration_minutes=90)
    new_activity = _make_activity(99, "Jazz Bar", category="nightlife")
    result_day, change = _apply_replace(day, block, new_activity, sample_preferences)

    assert "Jazz Bar" in change
    assert "Museum" in change
    assert result_day.blocks[0].activity.name == "Jazz Bar"
    assert result_day.blocks[0].start_time == block.start_time


# ─── _apply_add ──────────────────────────────────────────────────────────────

def test_apply_add_appends_to_end(sample_preferences):
    block = _make_block("Museum", end="2024-06-01T10:30:00")
    day = ItineraryDay(date="2024-06-01", blocks=[block], total_cost=30.0, total_duration_minutes=90)
    new_activity = _make_activity(99, "Rooftop Bar", category="nightlife")
    result_day, change = _apply_add(day, new_activity, sample_preferences)

    assert len(result_day.blocks) == 2
    assert result_day.blocks[-1].activity.name == "Rooftop Bar"
    # New block should start where previous ended
    assert result_day.blocks[-1].start_time == "2024-06-01T10:30:00"
    assert "Rooftop Bar" in change


# ─── _resolve_candidates ─────────────────────────────────────────────────────

def test_resolve_candidates_llm_suggestions_take_priority(sample_preferences):
    activities = [
        _make_activity(1, "Museum", "culture"),
        _make_activity(2, "Jazz Club", "nightlife"),
        _make_activity(3, "Beach", "beaches"),
    ]
    by_name = {a.name: a for a in activities}
    intent = RefinementIntent(
        action="replace", target_day=1, target_activity_name="Museum",
        desired_categories=["nightlife"], avoid_categories=[],
        replacement_candidates=["Jazz Club"],
        venue_search_query=None, explanation="",
    )
    result = _resolve_candidates(intent, activities, by_name, sample_preferences)
    assert len(result) == 1
    assert result[0].name == "Jazz Club"


def test_resolve_candidates_filters_by_category(sample_preferences):
    activities = [
        _make_activity(1, "Museum", "culture"),
        _make_activity(2, "Jazz Club", "nightlife"),
        _make_activity(3, "Beach", "beaches"),
    ]
    by_name = {a.name: a for a in activities}
    intent = RefinementIntent(
        action="replace", target_day=1, target_activity_name=None,
        desired_categories=["nightlife"], avoid_categories=[],
        replacement_candidates=[],
        venue_search_query=None, explanation="",
    )
    result = _resolve_candidates(intent, activities, by_name, sample_preferences)
    assert all(a.category == "nightlife" for a in result)


def test_resolve_candidates_excludes_target(sample_preferences):
    activities = [
        _make_activity(1, "Museum", "culture"),
        _make_activity(2, "Temple", "culture"),
    ]
    by_name = {a.name: a for a in activities}
    intent = RefinementIntent(
        action="replace", target_day=1, target_activity_name="Museum",
        desired_categories=["culture"], avoid_categories=[],
        replacement_candidates=[],
        venue_search_query=None, explanation="",
    )
    result = _resolve_candidates(intent, activities, by_name, sample_preferences)
    names = [a.name for a in result]
    assert "Museum" not in names
    assert "Temple" in names


# ─── _pick_best_candidate ────────────────────────────────────────────────────

def test_pick_best_candidate_returns_highest_score(sample_preferences):
    candidates = [
        _make_activity(1, "Low Rating", rating=2.0),
        _make_activity(2, "High Rating", rating=5.0),
        _make_activity(3, "Mid Rating", rating=3.5),
    ]
    slot_info = {"available_time_minutes": 480, "current_cost": 0.0}
    best = _pick_best_candidate(candidates, slot_info, sample_preferences, None, set())
    assert best is not None
    assert best.name == "High Rating"


def test_pick_best_candidate_skips_already_used(sample_preferences):
    candidates = [
        _make_activity(1, "Used Activity", rating=5.0),
        _make_activity(2, "Available Activity", rating=4.0),
    ]
    slot_info = {"available_time_minutes": 480, "current_cost": 0.0}
    already_used = {"Used Activity"}
    best = _pick_best_candidate(candidates, slot_info, sample_preferences, None, already_used)
    assert best is not None
    assert best.name == "Available Activity"


def test_pick_best_candidate_skips_too_long(sample_preferences):
    candidates = [
        _make_activity(1, "Too Long", duration=600, rating=5.0),
        _make_activity(2, "Just Right", duration=60, rating=3.5),
    ]
    slot_info = {"available_time_minutes": 90, "current_cost": 0.0}
    best = _pick_best_candidate(candidates, slot_info, sample_preferences, None, set())
    assert best is not None
    assert best.name == "Just Right"


def test_pick_best_candidate_none_when_all_too_long(sample_preferences):
    candidates = [_make_activity(1, "Too Long", duration=600, rating=5.0)]
    slot_info = {"available_time_minutes": 30, "current_cost": 0.0}
    best = _pick_best_candidate(candidates, slot_info, sample_preferences, None, set())
    assert best is None


# ─── _is_global_restructure ──────────────────────────────────────────────────

def test_is_global_restructure_detects_keywords():
    intent = RefinementIntent(
        action="replace", target_day=None, target_activity_name=None,
        desired_categories=[], avoid_categories=[], replacement_candidates=[],
        venue_search_query=None, explanation="",
    )
    assert _is_global_restructure(intent, "give me only 3 activities per day") is True
    assert _is_global_restructure(intent, "make each day less busy") is True
    assert _is_global_restructure(intent, "I want activities every day") is True


def test_is_global_restructure_ignores_specific_requests():
    intent = RefinementIntent(
        action="replace", target_day=2, target_activity_name="Museum",
        desired_categories=["nightlife"], avoid_categories=[], replacement_candidates=[],
        venue_search_query=None, explanation="",
    )
    assert _is_global_restructure(intent, "replace the museum on day 2 with nightlife") is False


# ─── _apply_global_trim ──────────────────────────────────────────────────────

def test_apply_global_trim_reduces_activities():
    blocks = [
        _make_block("A", start="2024-06-01T09:00:00", end="2024-06-01T10:00:00"),
        _make_block("B", start="2024-06-01T10:00:00", end="2024-06-01T11:00:00"),
        _make_block("C", start="2024-06-01T11:00:00", end="2024-06-01T12:00:00"),
        _make_block("D", start="2024-06-01T12:00:00", end="2024-06-01T13:00:00"),
    ]
    itinerary = _make_itinerary(blocks_day1=blocks)
    intent = RefinementIntent(
        action="replace", target_day=None, target_activity_name=None,
        desired_categories=[], avoid_categories=[], replacement_candidates=[],
        venue_search_query=None, explanation="",
    )
    result = _apply_global_trim(intent, itinerary, "only 2 activities per day")
    assert len(result.itinerary.days[0].blocks) == 2


def test_apply_global_trim_keeps_highest_rated():
    blocks = [
        _make_block("Low Rated", rating=2.0, start="2024-06-01T09:00:00", end="2024-06-01T10:00:00"),
        _make_block("High Rated", rating=5.0, start="2024-06-01T10:00:00", end="2024-06-01T11:00:00"),
        _make_block("Mid Rated", rating=3.5, start="2024-06-01T11:00:00", end="2024-06-01T12:00:00"),
    ]
    itinerary = _make_itinerary(blocks_day1=blocks)
    intent = RefinementIntent(
        action="replace", target_day=None, target_activity_name=None,
        desired_categories=[], avoid_categories=[], replacement_candidates=[],
        venue_search_query=None, explanation="",
    )
    result = _apply_global_trim(intent, itinerary, "only 1 activity per day")
    assert len(result.itinerary.days[0].blocks) == 1
    assert result.itinerary.days[0].blocks[0].activity.name == "High Rated"


# ─── _graceful_error ─────────────────────────────────────────────────────────

def test_graceful_error_returns_original_itinerary():
    itinerary = _make_itinerary()
    intent = RefinementIntent(
        action="replace", target_day=1, target_activity_name="Museum",
        desired_categories=[], avoid_categories=[], replacement_candidates=[],
        venue_search_query=None, explanation="",
    )
    result = _graceful_error(intent, itinerary, "Something went wrong.")
    assert result.itinerary == itinerary
    assert result.changes_made == []
    assert "Something went wrong." in result.assistant_message
