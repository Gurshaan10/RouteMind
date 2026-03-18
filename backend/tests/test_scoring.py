"""Tests for the scoring engine."""
import pytest
from app.core.scoring import (
    score_activity,
    haversine_distance,
    estimate_travel_time,
    get_budget_threshold,
)
from app.api.schemas import TripPreferences, BudgetLevel, EnergyLevel, TravelMode, Category
from app.db.models import Activity
from datetime import date, time


@pytest.fixture
def sample_activity():
    """Create a sample activity for testing."""
    activity = Activity(
        id=1,
        city_id=1,
        name="Test Activity",
        category="culture",
        base_cost=25.0,
        avg_duration_minutes=120,
        rating=4.5,
        latitude=37.7749,
        longitude=-122.4194,
        open_time=time(9, 0),
        close_time=time(17, 0),
        description="Test activity description"
    )
    return activity


@pytest.fixture
def sample_preferences():
    """Create sample trip preferences."""
    return TripPreferences(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 3),
        destination_city_id=1,
        trip_type="weekend",
        budget_level=BudgetLevel.medium,
        preferred_categories=[Category.culture, Category.food],
        energy_level=EnergyLevel.moderate,
        travel_mode=TravelMode.mixed,
    )


def test_haversine_distance():
    """Test Haversine distance calculation."""
    # Distance between San Francisco and Oakland (approximately 12 km)
    distance = haversine_distance(37.7749, -122.4194, 37.8044, -122.2711)
    assert 10 < distance < 15  # Should be around 12 km


def test_estimate_travel_time():
    """Test travel time estimation."""
    # 10 km distance
    walking_time = estimate_travel_time(10.0, TravelMode.walking)
    assert walking_time > 0
    assert walking_time < 200  # Should be reasonable
    
    # Taxi should be faster than walking
    taxi_time = estimate_travel_time(10.0, TravelMode.taxi)
    assert taxi_time < walking_time


def test_get_budget_threshold():
    """Test budget threshold calculation."""
    # Test with budget level
    assert get_budget_threshold("low", None) == 50.0
    assert get_budget_threshold("medium", None) == 150.0
    assert get_budget_threshold("high", None) == 300.0
    
    # Test with explicit budget
    assert get_budget_threshold("medium", 200.0) == 200.0


def test_score_activity_rating(sample_activity, sample_preferences):
    """Test that rating affects score."""
    day_state = {"current_cost": 0.0, "available_time_minutes": 480}
    
    score = score_activity(sample_activity, sample_preferences, day_state)
    assert score > 0
    
    # Higher rating should give higher score
    high_rating_activity = Activity(
        id=2,
        city_id=1,
        name="High Rating",
        category="culture",
        base_cost=25.0,
        avg_duration_minutes=120,
        rating=5.0,  # Higher rating
        latitude=37.7749,
        longitude=-122.4194,
        open_time=time(9, 0),
        close_time=time(17, 0),
    )
    high_score = score_activity(high_rating_activity, sample_preferences, day_state)
    assert high_score >= score


def test_score_activity_category_match(sample_preferences):
    """Test that preferred categories get bonus points."""
    day_state = {"current_cost": 0.0, "available_time_minutes": 480}
    
    # Activity in preferred category
    preferred_activity = Activity(
        id=1,
        city_id=1,
        name="Culture Activity",
        category="culture",  # In preferred list
        base_cost=25.0,
        avg_duration_minutes=120,
        rating=4.0,
        latitude=37.7749,
        longitude=-122.4194,
        open_time=time(9, 0),
        close_time=time(17, 0),
    )
    
    # Activity not in preferred category
    non_preferred_activity = Activity(
        id=2,
        city_id=1,
        name="Other Activity",
        category="adventure",  # Not in preferred list
        base_cost=25.0,
        avg_duration_minutes=120,
        rating=4.0,
        latitude=37.7749,
        longitude=-122.4194,
        open_time=time(9, 0),
        close_time=time(17, 0),
    )
    
    preferred_score = score_activity(preferred_activity, sample_preferences, day_state)
    non_preferred_score = score_activity(non_preferred_activity, sample_preferences, day_state)
    
    assert preferred_score > non_preferred_score


def test_score_activity_budget_penalty(sample_preferences):
    """Test that exceeding budget reduces score."""
    day_state_low_cost = {"current_cost": 0.0, "available_time_minutes": 480}
    day_state_high_cost = {"current_cost": 200.0, "available_time_minutes": 480}

    expensive_activity = Activity(
        id=1,
        city_id=1,
        name="Expensive Activity",
        category="culture",
        base_cost=100.0,  # Expensive
        avg_duration_minutes=120,
        rating=4.5,
        latitude=37.7749,
        longitude=-122.4194,
        open_time=time(9, 0),
        close_time=time(17, 0),
    )

    score_low_cost = score_activity(expensive_activity, sample_preferences, day_state_low_cost)
    score_high_cost = score_activity(expensive_activity, sample_preferences, day_state_high_cost)

    # Score should be lower when already over budget
    assert score_high_cost <= score_low_cost


def test_score_activity_travel_penalty(sample_preferences):
    """Test that far-away activities get penalized more than nearby ones."""
    day_state = {"current_cost": 0.0, "available_time_minutes": 480}

    previous_activity = Activity(
        id=10, city_id=1, name="Start", category="culture",
        base_cost=0.0, avg_duration_minutes=60, rating=4.0,
        latitude=37.7749, longitude=-122.4194,
    )

    nearby_activity = Activity(
        id=2, city_id=1, name="Nearby", category="culture",
        base_cost=20.0, avg_duration_minutes=60, rating=4.0,
        latitude=37.7760, longitude=-122.4200,  # ~0.1 km away
    )

    far_activity = Activity(
        id=3, city_id=1, name="Far Away", category="culture",
        base_cost=20.0, avg_duration_minutes=60, rating=4.0,
        latitude=37.9000, longitude=-122.5000,  # ~18 km away
    )

    nearby_score = score_activity(nearby_activity, sample_preferences, day_state, previous_activity=previous_activity)
    far_score = score_activity(far_activity, sample_preferences, day_state, previous_activity=previous_activity)

    assert nearby_score > far_score


def test_score_activity_must_visit_boost(sample_preferences):
    """Test that must-visit constraint gives a large score boost."""
    from app.api.schemas import Constraints

    day_state = {"current_cost": 0.0, "available_time_minutes": 480}

    activity = Activity(
        id=1, city_id=1, name="Special Place", category="adventure",
        base_cost=50.0, avg_duration_minutes=120, rating=3.5,
        latitude=37.7749, longitude=-122.4194,
    )

    # Without must-visit
    prefs_normal = sample_preferences
    score_normal = score_activity(activity, prefs_normal, day_state)

    # With must-visit
    prefs_must_visit = TripPreferences(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 3),
        destination_city_id=1,
        trip_type="weekend",
        budget_level=BudgetLevel.medium,
        preferred_categories=[Category.culture, Category.food],
        energy_level=EnergyLevel.moderate,
        travel_mode=TravelMode.mixed,
        constraints=Constraints(must_visit=["Special Place"]),
    )
    score_must = score_activity(activity, prefs_must_visit, day_state)

    assert score_must > score_normal + 40  # Must-visit adds 50 points


def test_score_activity_avoid_gives_negative(sample_preferences):
    """Test that avoided activities get a score of 0 (clamped from -100)."""
    from app.api.schemas import Constraints

    day_state = {"current_cost": 0.0, "available_time_minutes": 480}

    activity = Activity(
        id=1, city_id=1, name="Bad Place", category="culture",
        base_cost=20.0, avg_duration_minutes=60, rating=4.9,
        latitude=37.7749, longitude=-122.4194,
    )

    prefs_avoid = TripPreferences(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 3),
        destination_city_id=1,
        trip_type="weekend",
        budget_level=BudgetLevel.medium,
        preferred_categories=[],
        energy_level=EnergyLevel.moderate,
        travel_mode=TravelMode.mixed,
        constraints=Constraints(avoid=["Bad Place"]),
    )
    score = score_activity(activity, prefs_avoid, day_state)
    assert score == 0.0  # Clamped from -100


def test_score_activity_explain_returns_tuple(sample_activity, sample_preferences):
    """Test that explain=True returns a (score, SelectionExplanation) tuple."""
    from app.api.schemas import SelectionExplanation

    day_state = {"current_cost": 0.0, "available_time_minutes": 480}
    result = score_activity(sample_activity, sample_preferences, day_state, explain=True)

    assert isinstance(result, tuple)
    assert len(result) == 2
    score, explanation = result
    assert isinstance(score, float)
    assert isinstance(explanation, SelectionExplanation)
    assert explanation.summary != ""


def test_haversine_same_point():
    """Distance from a point to itself should be 0."""
    assert haversine_distance(37.7749, -122.4194, 37.7749, -122.4194) == 0.0


def test_estimate_travel_time_walking_slower_than_taxi():
    """Walking should always take longer than taxi for the same distance."""
    distance = 5.0
    walking = estimate_travel_time(distance, TravelMode.walking)
    taxi = estimate_travel_time(distance, TravelMode.taxi)
    assert walking > taxi


def test_get_budget_threshold_explicit_overrides_level():
    """Explicit budget_per_day always wins over budget_level."""
    result = get_budget_threshold("low", 250.0)
    assert result == 250.0

