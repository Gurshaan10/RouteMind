"""LLM narrative generator for itineraries."""
from app.llm.client import LLMClient
from app.api.schemas import TripPreferences, NarrativeResult
from app.core.optimizer import Itinerary


def format_itinerary_for_llm(itinerary: Itinerary) -> str:
    """Format itinerary data into a compact string for LLM."""
    lines = []
    
    if itinerary.summary:
        lines.append(f"Trip Summary:")
        lines.append(f"- Total Cost: ${itinerary.summary.total_cost:.2f}")
        lines.append(f"- Average Cost per Day: ${itinerary.summary.avg_cost_per_day:.2f}")
        lines.append(f"- Categories Covered: {', '.join(itinerary.summary.categories_covered)}")
        lines.append(f"- Pace: {itinerary.summary.pace_label}")
        lines.append("")
    
    for day in itinerary.days:
        lines.append(f"Day {day.date}:")
        for i, block in enumerate(day.blocks):
            time_str = block.start_time.split("T")[1][:5]  # Extract time
            lines.append(
                f"  {time_str} - {block.activity.name} ({block.activity.category})"
            )
            if block.travel_time_from_previous:
                lines.append(f"    (Travel time: {block.travel_time_from_previous} minutes)")
        lines.append("")
    
    return "\n".join(lines)


def format_preferences_for_llm(preferences: TripPreferences) -> str:
    """Format user preferences into a string for LLM."""
    lines = []
    lines.append("User Preferences:")
    lines.append(f"- Trip Type: {preferences.trip_type.value}")
    lines.append(f"- Budget Level: {preferences.budget_level.value}")
    if preferences.budget_per_day:
        lines.append(f"- Budget per Day: ${preferences.budget_per_day:.2f}")
    lines.append(f"- Energy Level: {preferences.energy_level.value}")
    lines.append(f"- Travel Mode: {preferences.travel_mode.value}")
    
    if preferences.preferred_categories:
        categories = [cat.value for cat in preferences.preferred_categories]
        lines.append(f"- Preferred Categories: {', '.join(categories)}")
    
    if preferences.constraints:
        if preferences.constraints.must_visit:
            lines.append(f"- Must Visit: {', '.join(preferences.constraints.must_visit)}")
        if preferences.constraints.avoid:
            lines.append(f"- Avoid: {', '.join(preferences.constraints.avoid)}")
        if preferences.constraints.dietary_preferences:
            lines.append(f"- Dietary: {preferences.constraints.dietary_preferences}")
    
    return "\n".join(lines)


async def generate_narrative(
    itinerary: Itinerary, preferences: TripPreferences
) -> NarrativeResult:
    """
    Generate narrative text for an itinerary using LLM.
    
    Args:
        itinerary: The optimized itinerary
        preferences: User trip preferences
    
    Returns:
        NarrativeResult with narrative text, explanations, and tips
    """
    client = LLMClient()
    
    system_prompt = """You are a concise travel assistant. Write a short, punchy trip overview — no more than 3-4 sentences. Then give 2-3 practical bullet-point tips specific to this trip. Do NOT recap the day-by-day schedule (it's already shown below). Be warm but brief."""

    itinerary_text = format_itinerary_for_llm(itinerary)
    preferences_text = format_preferences_for_llm(preferences)

    user_prompt = f"""Trip details:
{preferences_text}

{itinerary_text}

Write:
1. A 3-4 sentence intro that captures the vibe of this trip and gets the traveler excited.
2. 2-3 short practical tips (packing, timing, money, local customs, etc.) specific to this destination and trip style.

Keep the total response under 150 words. No day-by-day recap."""
    
    # Generate narrative
    narrative_text = await client.generate_completion(system_prompt, user_prompt)
    
    # For now, we'll put everything in narrative_text
    # In a more advanced version, we could parse the LLM response to extract
    # separate explanations and tips sections
    
    return NarrativeResult(
        narrative_text=narrative_text,
        explanations=None,  # Could be extracted from LLM response
        tips=None,  # Could be extracted from LLM response
    )

