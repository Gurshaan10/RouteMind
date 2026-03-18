"""Tests for the itinerary optimizer."""
import pytest
from datetime import date, time, timedelta
from app.core.optimizer import (
    build_itinerary,
    get_activities_per_day,
    is_activity_available,
)
from app.api.schemas import (
    TripPreferences,
    BudgetLevel,
    EnergyLevel,
    TravelMode,
    Category,
)
from app.db.models import Activity, City


@pytest.fixture
def sample_city():
    """Create a sample city."""
    return City(
        id=1,
        name="Test City",
        country="Test Country",
        time_zone="UTC",
        default_currency="USD"
    )


@pytest.fixture
def sample_activities(sample_city):
    """Create sample activities for testing."""
    return [
        Activity(
            id=1,
            city_id=sample_city.id,
            name="Morning Activity",
            category="culture",
            base_cost=20.0,
            avg_duration_minutes=120,
            rating=4.5,
            latitude=37.7749,
            longitude=-122.4194,
            open_time=time(9, 0),
            close_time=time(17, 0),
        ),
        Activity(
            id=2,
            city_id=sample_city.id,
            name="Afternoon Activity",
            category="food",
            base_cost=30.0,
            avg_duration_minutes=90,
            rating=4.7,
            latitude=37.7849,
            longitude=-122.4094,
            open_time=time(11, 0),
            close_time=time(20, 0),
        ),
        Activity(
            id=3,
            city_id=sample_city.id,
            name="Evening Activity",
            category="nature",
            base_cost=0.0,
            avg_duration_minutes=60,
            rating=4.3,
            latitude=37.7649,
            longitude=-122.4294,
            open_time=None,  # Always open
            close_time=None,
        ),
    ]


@pytest.fixture
def sample_preferences():
    """Create sample trip preferences."""
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


def test_get_activities_per_day():
    """Test activity count per day based on energy level."""
    relaxed_min, relaxed_max = get_activities_per_day(EnergyLevel.relaxed)
    assert relaxed_min == 2
    assert relaxed_max == 3
    
    moderate_min, moderate_max = get_activities_per_day(EnergyLevel.moderate)
    assert moderate_min == 3
    assert moderate_max == 5
    
    active_min, active_max = get_activities_per_day(EnergyLevel.active)
    assert active_min == 5
    assert active_max == 7


def test_is_activity_available():
    """Test activity availability checking."""
    from datetime import datetime
    
    # Activity with hours
    activity_with_hours = Activity(
        id=1,
        city_id=1,
        name="Test",
        category="culture",
        base_cost=0.0,
        avg_duration_minutes=60,
        rating=4.0,
        latitude=37.7749,
        longitude=-122.4194,
        open_time=time(9, 0),
        close_time=time(17, 0),
    )
    
    # Activity always open
    activity_always_open = Activity(
        id=2,
        city_id=1,
        name="Test",
        category="culture",
        base_cost=0.0,
        avg_duration_minutes=60,
        rating=4.0,
        latitude=37.7749,
        longitude=-122.4194,
        open_time=None,
        close_time=None,
    )
    
    # Test during open hours
    current_time = datetime(2024, 6, 1, 12, 0)  # Noon
    assert is_activity_available(activity_with_hours, current_time) == True
    
    # Test outside open hours
    current_time = datetime(2024, 6, 1, 20, 0)  # 8 PM
    assert is_activity_available(activity_with_hours, current_time) == False
    
    # Always open activity
    assert is_activity_available(activity_always_open, current_time) == True


def test_build_itinerary_basic(sample_preferences, sample_activities):
    """Test basic itinerary building."""
    itinerary = build_itinerary(sample_preferences, sample_activities)
    
    assert itinerary is not None
    assert len(itinerary.days) > 0
    assert itinerary.summary is not None
    assert itinerary.optimization_score >= 0
    assert itinerary.confidence_score >= 0


def test_build_itinerary_respects_energy_level(sample_preferences, sample_activities):
    """Test that itinerary respects energy level."""
    # Test relaxed energy level
    relaxed_prefs = TripPreferences(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 1),
        destination_city_id=1,
        trip_type="day_trip",
        budget_level=BudgetLevel.medium,
        preferred_categories=[],
        energy_level=EnergyLevel.relaxed,
        travel_mode=TravelMode.mixed,
    )
    
    itinerary = build_itinerary(relaxed_prefs, sample_activities)
    if itinerary.days:
        activities_per_day = len(itinerary.days[0].blocks)
        assert activities_per_day <= 3  # Relaxed: max 3 activities


def test_build_itinerary_respects_budget(sample_activities):
    """Test that itinerary respects budget constraints."""
    low_budget_prefs = TripPreferences(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 1),
        destination_city_id=1,
        trip_type="day_trip",
        budget_level=BudgetLevel.low,
        budget_per_day=50.0,
        preferred_categories=[],
        energy_level=EnergyLevel.moderate,
        travel_mode=TravelMode.mixed,
    )
    
    itinerary = build_itinerary(low_budget_prefs, sample_activities)
    if itinerary.days and itinerary.summary:
        # Total cost should be reasonable for low budget
        assert itinerary.summary.total_cost <= 100.0  # Allow some flexibility


def test_build_itinerary_must_visit(sample_preferences, sample_activities):
    """Test that must-visit activities are included."""
    from app.api.schemas import Constraints

    prefs_with_must_visit = TripPreferences(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 1),
        destination_city_id=1,
        trip_type="day_trip",
        budget_level=BudgetLevel.medium,
        preferred_categories=[],
        energy_level=EnergyLevel.moderate,
        travel_mode=TravelMode.mixed,
        constraints=Constraints(must_visit=["Morning Activity"]),
    )

    itinerary = build_itinerary(prefs_with_must_visit, sample_activities)
    if itinerary.days:
        activity_names = [
            block.activity.name
            for day in itinerary.days
            for block in day.blocks
        ]
        assert "Morning Activity" in activity_names


def test_build_itinerary_no_duplicate_activities(sample_preferences, sample_activities):
    """Each activity should appear at most once across all days."""
    itinerary = build_itinerary(sample_preferences, sample_activities)
    all_names = [
        block.activity.name
        for day in itinerary.days
        for block in day.blocks
    ]
    assert len(all_names) == len(set(all_names)), "Duplicate activities found in itinerary"


def test_build_itinerary_chronological_order(sample_preferences, sample_activities):
    """Activities within a day must be in chronological order."""
    itinerary = build_itinerary(sample_preferences, sample_activities)
    for day in itinerary.days:
        times = [block.start_time for block in day.blocks]
        assert times == sorted(times), f"Day {day.date} activities are not in chronological order"


def test_build_itinerary_empty_activities(sample_preferences):
    """Optimizer should handle empty activity list gracefully."""
    itinerary = build_itinerary(sample_preferences, [])
    assert itinerary is not None
    # All days should have 0 blocks
    for day in itinerary.days:
        assert len(day.blocks) == 0


def test_build_itinerary_active_energy_more_activities(sample_activities):
    """Active energy level should produce more activities per day than relaxed."""
    relaxed_prefs = TripPreferences(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 1),
        destination_city_id=1,
        trip_type="day_trip",
        budget_level=BudgetLevel.high,
        preferred_categories=[],
        energy_level=EnergyLevel.relaxed,
        travel_mode=TravelMode.taxi,
    )
    active_prefs = TripPreferences(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 1),
        destination_city_id=1,
        trip_type="day_trip",
        budget_level=BudgetLevel.high,
        preferred_categories=[],
        energy_level=EnergyLevel.active,
        travel_mode=TravelMode.taxi,
    )

    relaxed_itinerary = build_itinerary(relaxed_prefs, sample_activities)
    active_itinerary = build_itinerary(active_prefs, sample_activities)

    if relaxed_itinerary.days and active_itinerary.days:
        relaxed_count = len(relaxed_itinerary.days[0].blocks)
        active_count = len(active_itinerary.days[0].blocks)
        # Active should have >= relaxed (can't always guarantee strictly more with small fixture)
        assert active_count >= relaxed_count


def test_build_itinerary_multi_day(sample_activities):
    """Multi-day trip should produce the correct number of day objects."""
    # Extend fixtures so there are enough activities to fill multiple days
    extra = [
        Activity(
            id=i, city_id=1, name=f"Activity {i}", category="food",
            base_cost=15.0, avg_duration_minutes=60, rating=4.0,
            latitude=37.77 + i * 0.001, longitude=-122.41,
        )
        for i in range(4, 15)
    ]
    all_activities = sample_activities + extra

    prefs = TripPreferences(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 3),  # 3 days
        destination_city_id=1,
        trip_type="weekend",
        budget_level=BudgetLevel.medium,
        preferred_categories=[],
        energy_level=EnergyLevel.moderate,
        travel_mode=TravelMode.mixed,
    )
    itinerary = build_itinerary(prefs, all_activities)
    assert len(itinerary.days) == 3


def test_get_activities_per_day_all_levels():
    """All energy levels should return valid (min, max) tuples with min <= max."""
    for level in [EnergyLevel.relaxed, EnergyLevel.moderate, EnergyLevel.active]:
        min_a, max_a = get_activities_per_day(level)
        assert min_a >= 1
        assert max_a >= min_a

