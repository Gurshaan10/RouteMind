"use client";

import { useState, useEffect } from "react";

interface City {
  id: number;
  name: string;
  country: string;
}

interface CityWithDays {
  city: City;
  days: number;
}

interface MultiCitySelectorProps {
  cities: City[];
  onPlanTrip: (cityIds: number[], totalDays: number, interests: string[], pace: string) => void;
  loading: boolean;
}

const CATEGORIES = [
  "food",
  "culture",
  "nightlife",
  "nature",
  "shopping",
  "adventure",
  "beaches",
] as const;

export default function MultiCitySelector({
  cities,
  onPlanTrip,
  loading,
}: MultiCitySelectorProps) {
  const [selectedCities, setSelectedCities] = useState<number[]>([]);
  const [totalDays, setTotalDays] = useState(7);
  const [interests, setInterests] = useState<string[]>([]);
  const [pace, setPace] = useState<"relaxed" | "moderate" | "packed">("moderate");
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [daysAllocation, setDaysAllocation] = useState<any[]>([]);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const toggleCity = (cityId: number) => {
    if (selectedCities.includes(cityId)) {
      setSelectedCities(selectedCities.filter((id) => id !== cityId));
    } else {
      if (selectedCities.length < 5) {
        setSelectedCities([...selectedCities, cityId]);
      }
    }
  };

  const toggleInterest = (category: string) => {
    if (interests.includes(category)) {
      setInterests(interests.filter((c) => c !== category));
    } else {
      setInterests([...interests, category]);
    }
  };

  // Fetch suggested days allocation when cities or total days change
  useEffect(() => {
    if (selectedCities.length >= 2) {
      fetchDaysAllocation();
    } else {
      setDaysAllocation([]);
    }
  }, [selectedCities, totalDays]);

  const fetchDaysAllocation = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/multi-city/suggest-days?city_ids=${selectedCities.join(",")}&total_days=${totalDays}`
      );
      if (response.ok) {
        const data = await response.json();
        setDaysAllocation(data.allocation || []);
      }
    } catch (error) {
      console.error("Failed to fetch days allocation:", error);
    }
  };

  const fetchRecommendations = async (baseCityId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/multi-city/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          base_city_id: baseCityId,
          num_recommendations: 3,
          interests: interests.length > 0 ? interests : null,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setRecommendations(data.recommendations || []);
        setShowRecommendations(true);
      }
    } catch (error) {
      console.error("Failed to fetch recommendations:", error);
    }
  };

  const handleSubmit = () => {
    if (selectedCities.length >= 2) {
      onPlanTrip(selectedCities, totalDays, interests, pace);
    }
  };

  const selectedCityObjects = cities.filter((city) =>
    selectedCities.includes(city.id)
  );

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-800">
          Multi-City Trip Planner
        </h2>
        <span className="text-sm text-gray-500">
          Select 2-5 cities to visit
        </span>
      </div>

      {/* City Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Select Cities ({selectedCities.length}/5)
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {cities.map((city) => {
            const isSelected = selectedCities.includes(city.id);
            return (
              <button
                key={city.id}
                onClick={() => toggleCity(city.id)}
                disabled={!isSelected && selectedCities.length >= 5}
                className={`p-3 rounded-lg border-2 transition-all ${
                  isSelected
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : selectedCities.length >= 5
                    ? "border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed"
                    : "border-gray-200 hover:border-blue-300 hover:bg-blue-50"
                }`}
              >
                <div className="font-semibold text-sm">{city.name}</div>
                <div className="text-xs text-gray-500">{city.country}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Show recommendations button if at least one city selected */}
      {selectedCities.length >= 1 && selectedCities.length < 5 && (
        <div className="mb-6">
          <button
            onClick={() => fetchRecommendations(selectedCities[0])}
            className="text-sm text-blue-600 hover:text-blue-700 underline"
          >
            Get city recommendations based on {selectedCityObjects[0]?.name}
          </button>
        </div>
      )}

      {/* Recommendations */}
      {showRecommendations && recommendations.length > 0 && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-700">
              Recommended Cities
            </h3>
            <button
              onClick={() => setShowRecommendations(false)}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              Hide
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {recommendations.map((rec) => (
              <div
                key={rec.city_id}
                className="p-3 bg-white rounded-lg border border-gray-200"
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="font-semibold text-sm">{rec.city_name}</div>
                    <div className="text-xs text-gray-500">{rec.country}</div>
                  </div>
                  <button
                    onClick={() => toggleCity(rec.city_id)}
                    disabled={
                      selectedCities.includes(rec.city_id) ||
                      selectedCities.length >= 5
                    }
                    className={`px-2 py-1 text-xs rounded ${
                      selectedCities.includes(rec.city_id)
                        ? "bg-gray-100 text-gray-400"
                        : "bg-blue-500 text-white hover:bg-blue-600"
                    }`}
                  >
                    {selectedCities.includes(rec.city_id) ? "Added" : "Add"}
                  </button>
                </div>
                <p className="text-xs text-gray-600 mb-2">{rec.reason}</p>
                <div className="text-xs text-gray-500">
                  {rec.total_activities} activities
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Selected Cities Summary with Days Allocation */}
      {selectedCities.length >= 2 && (
        <div className="mb-6 p-4 bg-green-50 rounded-lg border border-green-200">
          <h3 className="text-sm font-semibold text-green-800 mb-3">
            Your Trip Route
          </h3>
          <div className="space-y-2">
            {daysAllocation.length > 0 ? (
              daysAllocation.map((allocation, index) => (
                <div key={allocation.city_id} className="flex items-center gap-2">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-600 text-white flex items-center justify-center text-sm font-bold">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-green-900">
                      {allocation.city_name}
                    </div>
                  </div>
                  <div className="text-sm text-green-700 font-semibold">
                    {allocation.suggested_days} {allocation.suggested_days === 1 ? "day" : "days"}
                  </div>
                </div>
              ))
            ) : (
              selectedCityObjects.map((city, index) => (
                <div key={city.id} className="flex items-center gap-2">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-600 text-white flex items-center justify-center text-sm font-bold">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-green-900">{city.name}</div>
                    <div className="text-xs text-green-700">{city.country}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Trip Configuration */}
      {selectedCities.length >= 2 && (
        <>
          {/* Total Days */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Total Trip Duration: {totalDays} days
            </label>
            <input
              type="range"
              min="4"
              max="30"
              value={totalDays}
              onChange={(e) => setTotalDays(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-500"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>4 days</span>
              <span>30 days</span>
            </div>
          </div>

          {/* Interests */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Interests (Optional)
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {CATEGORIES.map((category) => {
                const isSelected = interests.includes(category);
                return (
                  <button
                    key={category}
                    onClick={() => toggleInterest(category)}
                    className={`px-3 py-2 rounded-lg border text-sm capitalize transition-all ${
                      isSelected
                        ? "border-blue-500 bg-blue-500 text-white"
                        : "border-gray-300 hover:border-blue-400"
                    }`}
                  >
                    {category}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Pace */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Trip Pace
            </label>
            <div className="grid grid-cols-3 gap-3">
              {(["relaxed", "moderate", "packed"] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPace(p)}
                  className={`px-4 py-3 rounded-lg border-2 text-sm capitalize transition-all ${
                    pace === p
                      ? "border-blue-500 bg-blue-50 text-blue-700 font-semibold"
                      : "border-gray-200 hover:border-blue-300"
                  }`}
                >
                  <div className="font-medium">{p}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {p === "relaxed" && "2-3 activities/day"}
                    {p === "moderate" && "4-5 activities/day"}
                    {p === "packed" && "6+ activities/day"}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={loading || selectedCities.length < 2}
            className={`w-full py-3 px-6 rounded-lg font-semibold text-white transition-all ${
              loading || selectedCities.length < 2
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg
                  className="animate-spin h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Planning your trip...
              </span>
            ) : (
              `Plan ${selectedCities.length}-City Trip`
            )}
          </button>
        </>
      )}

      {/* Help text */}
      {selectedCities.length < 2 && selectedCities.length > 0 && (
        <p className="text-sm text-gray-500 text-center mt-4">
          Select at least one more city to start planning your multi-city adventure
        </p>
      )}
    </div>
  );
}
