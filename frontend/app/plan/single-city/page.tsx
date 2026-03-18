"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession, signIn } from "next-auth/react";
import dynamic from "next/dynamic";
import Toast from "../../components/Toast";
import ActivityModal from "../../components/ActivityModal";
import { api } from "../../lib/api";
import { getSessionId } from "../../lib/session";
import { useItineraryStore } from "../../store/itineraryStore";

// Dynamic imports to avoid SSR issues
const GoogleItineraryMap = dynamic(() => import("../../components/GoogleItineraryMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-96 bg-gray-100 rounded-lg flex items-center justify-center">
      <p className="text-gray-500">Loading map...</p>
    </div>
  ),
});

const WorldMapSelector = dynamic(() => import("@/components/WorldMapSelector"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-96 glass-card rounded-lg flex items-center justify-center">
      <p className="text-gray-300">Loading world map...</p>
    </div>
  ),
});

interface City {
  id: number;
  name: string;
  country: string;
  time_zone: string;
  default_currency: string;
}

interface TripPreferences {
  start_date: string;
  end_date: string;
  destination_city_id: number;
  trip_type: "day_trip" | "weekend" | "one_week" | "long";
  budget_level: "low" | "medium" | "high";
  budget_per_day?: number;
  preferred_categories: string[];
  energy_level: "relaxed" | "moderate" | "active";
  travel_mode: "walking" | "public_transport" | "taxi" | "self_drive" | "mixed";
  constraints?: {
    must_visit?: string[];
    avoid?: string[];
    dietary_preferences?: string;
    walking_tolerance?: "low" | "medium" | "high";
  };
}

interface VenueAlternative {
  name: string;
  category: string;
  rating: number;
  address: string;
  latitude: number;
  longitude: number;
  cost: number;
  price_label: string;
  place_id: string;
  source: string;
}

interface SelectionExplanation {
  category_match: boolean;
  budget_fit: string;
  time_fit: string;
  travel_proximity: string;
  rating_quality: string;
  must_visit: boolean;
  summary: string;
  semantic_relevance_score?: number | null;
}

interface ActivitySummary {
  id: number;
  name: string;
  category: string;
  cost: number;
  duration: number;
  rating: number;
  coordinates: {
    latitude: number;
    longitude: number;
  };
  tags?: string[] | null;
  description?: string | null;
  explanation?: SelectionExplanation | null;
}

interface ItineraryBlock {
  start_time: string;
  end_time: string;
  activity: ActivitySummary;
  travel_time_from_previous?: number;
  notes?: string;
}

interface ItineraryDay {
  date: string;
  total_cost: number;
  total_duration_minutes: number;
  blocks: ItineraryBlock[];
}

interface ItineraryResponse {
  days: ItineraryDay[];
  summary: {
    total_cost: number;
    avg_cost_per_day: number;
    categories_covered: string[];
    pace_label: string;
  };
  optimization_score: number;
  confidence_score: number;
  narrative: {
    narrative_text: string;
    explanations?: string;
    tips?: string;
  };
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const CATEGORIES = [
  "food",
  "culture",
  "nightlife",
  "nature",
  "shopping",
  "adventure",
  "beaches",
] as const;

interface ToastState {
  message: string;
  type: "error" | "success" | "info";
}

type Step = "select-city" | "preferences" | "result";

const LOADING_STEPS = [
  { label: "Finding activities", icon: "🔍" },
  { label: "Optimizing your schedule", icon: "⚡" },
  { label: "Crafting your narrative", icon: "✨" },
  { label: "Almost ready...", icon: "🎉" },
];

function LoadingProgress({ cityName }: { cityName?: string }) {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => Math.min(prev + 1, LOADING_STEPS.length - 1));
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  const progress = ((activeStep + 1) / LOADING_STEPS.length) * 100;

  return (
    <div className="glass-card rounded-2xl p-10 flex flex-col items-center justify-center min-h-[340px]">
      <h2 className="text-2xl font-bold gradient-text mb-2">
        Planning your trip{cityName ? ` to ${cityName}` : ""}...
      </h2>
      <p className="text-gray-400 text-sm mb-8">This usually takes 10–20 seconds</p>

      {/* Progress bar */}
      <div className="w-full max-w-sm bg-gray-700 rounded-full h-2 mb-8 overflow-hidden">
        <div
          className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-700"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Steps */}
      <div className="w-full max-w-sm space-y-3">
        {LOADING_STEPS.map((step, i) => (
          <div key={i} className={`flex items-center gap-3 transition-opacity duration-500 ${i <= activeStep ? "opacity-100" : "opacity-30"}`}>
            <span className="text-xl w-8 text-center">
              {i < activeStep ? "✓" : i === activeStep ? step.icon : "○"}
            </span>
            <span className={`text-sm font-medium ${i < activeStep ? "text-green-400" : i === activeStep ? "text-white" : "text-gray-500"}`}>
              {step.label}
            </span>
            {i === activeStep && (
              <span className="ml-auto">
                <span className="inline-block w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function SingleCityPlanner() {
  const router = useRouter();
  const { data: session } = useSession();
  const [currentStep, setCurrentStep] = useState<Step>("select-city");
  const [cities, setCities] = useState<City[]>([]);
  const [loading, setLoading] = useState(false);
  const [itinerary, setItinerary] = useState<ItineraryResponse | null>(null);
  const [toast, setToast] = useState<ToastState | null>(null);
  const [selectedActivity, setSelectedActivity] = useState<ActivitySummary | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isSharing, setIsSharing] = useState(false);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [refineMessage, setRefineMessage] = useState("");
  const [isRefining, setIsRefining] = useState(false);
  const [refineResult, setRefineResult] = useState<string | null>(null);
  const [refineAlternatives, setRefineAlternatives] = useState<VenueAlternative[] | null>(null);
  const [activeDayIndex, setActiveDayIndex] = useState(0);
  const [formData, setFormData] = useState<Partial<TripPreferences>>({
    trip_type: "weekend",
    budget_level: "medium",
    energy_level: "moderate",
    travel_mode: "mixed",
    preferred_categories: [],
  });

  // Zustand store
  const { setCurrentSavedId } = useItineraryStore();

  useEffect(() => {
    fetchCities();
  }, []);

  const fetchCities = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/cities`);
      if (response.ok) {
        const data = await response.json();
        setCities(data);
      }
    } catch (error) {
      console.error("Failed to fetch cities:", error);
    }
  };

  const handleCitySelect = (cityId: number) => {
    setFormData({ ...formData, destination_city_id: cityId });
  };

  const handleCityDeselect = () => {
    setFormData({ ...formData, destination_city_id: undefined });
  };

  const handleCityConfirm = (_cityId: number) => {
    setCurrentStep("preferences");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setItinerary(null);

    try {
      const authToken = (session as any)?.accessToken;
      const response = await fetch(`${API_BASE_URL}/api/v1/plan-itinerary`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-ID": getSessionId(),
          ...(authToken ? { "Authorization": `Bearer ${authToken}` } : {}),
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const error = await response.json();
        let errorMessage = "Failed to generate itinerary";

        if (error.detail) {
          if (typeof error.detail === "string") {
            errorMessage = error.detail;
          } else if (error.detail.message) {
            errorMessage = error.detail.message;
            if (error.detail.error_code === "INFEASIBLE_CONSTRAINTS" && error.detail.details) {
              const infeasible = Object.entries(error.detail.details)
                .map(([name, reason]) => `${name}: ${reason}`)
                .join(", ");
              errorMessage += ` (${infeasible})`;
            }
          }
        }

        setToast({ message: errorMessage, type: "error" });
        return;
      }

      const data = await response.json();
      setItinerary(data);
      setActiveDayIndex(0);
      setCurrentStep("result");
      setToast({ message: "Itinerary generated successfully!", type: "success" });
    } catch (error) {
      console.error("Error generating itinerary:", error);
      setToast({
        message: "Network error. Please check your connection and try again.",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleCategory = (category: string) => {
    const current = formData.preferred_categories || [];
    if (current.includes(category)) {
      setFormData({
        ...formData,
        preferred_categories: current.filter((c) => c !== category),
      });
    } else {
      setFormData({
        ...formData,
        preferred_categories: [...current, category],
      });
    }
  };

  const handleRefine = async () => {
    if (!itinerary || !refineMessage.trim() || !formData) return;
    setIsRefining(true);
    setRefineResult(null);
    setRefineAlternatives(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/refine-itinerary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          itinerary,
          preferences: {
            ...formData,
            start_date: formData.start_date,
            end_date: formData.end_date,
          },
          user_message: refineMessage,
        }),
      });
      if (response.ok) {
        const data = await response.json();
        setItinerary(data.itinerary);
        setActiveDayIndex(0);
        setRefineResult(data.assistant_message);
        setRefineAlternatives(data.alternatives || null);
        setRefineMessage("");
      } else {
        const err = await response.json();
        setRefineResult(`Could not apply: ${err.detail || "Unknown error"}`);
      }
    } catch (e) {
      setRefineResult("Request failed. Is the backend running?");
    } finally {
      setIsRefining(false);
    }
  };

  const handleShareItinerary = async () => {
    if (!itinerary) return;

    // Must be saved first before sharing
    if (!session) {
      setToast({
        message: "Sign in to save and share your itinerary!",
        type: "info"
      });
      setTimeout(() => signIn("google"), 1500);
      return;
    }

    setIsSharing(true);
    try {
      // First save the itinerary as public
      const authToken = (session as any)?.accessToken;

      const saveRequest = {
        trip_preferences: {
          start_date: formData.start_date,
          end_date: formData.end_date,
          destination_city_id: formData.destination_city_id,
          trip_type: formData.trip_type,
          budget_level: formData.budget_level,
          budget_per_day: formData.budget_per_day,
          preferred_categories: formData.preferred_categories || [],
          energy_level: formData.energy_level,
          travel_mode: formData.travel_mode,
          constraints: formData.constraints
        },
        itinerary: itinerary,
        is_public: true // Make it public for sharing
      };

      const savedItinerary = await api.saveItinerary(saveRequest, authToken);

      if (savedItinerary.share_url) {
        setShareUrl(savedItinerary.share_url);
        // Copy to clipboard
        await navigator.clipboard.writeText(savedItinerary.share_url);
        setToast({ message: "Share link copied to clipboard!", type: "success" });
      }
    } catch (error) {
      console.error("Share itinerary error:", error);
      setToast({ message: "Failed to create share link", type: "error" });
    } finally {
      setIsSharing(false);
    }
  };

  const handleSaveItinerary = async () => {
    if (!itinerary) return;

    // If not signed in, show prompt to sign in
    if (!session) {
      setToast({
        message: "Sign in to save your itinerary and access it from anywhere!",
        type: "info"
      });
      setTimeout(() => signIn("google"), 1500);
      return;
    }

    setIsSaving(true);
    try {
      // Get auth token from session
      const authToken = (session as any)?.accessToken;

      // Build the complete request matching backend schema
      const saveRequest = {
        trip_preferences: {
          start_date: formData.start_date,
          end_date: formData.end_date,
          destination_city_id: formData.destination_city_id,
          trip_type: formData.trip_type,
          budget_level: formData.budget_level,
          budget_per_day: formData.budget_per_day,
          preferred_categories: formData.preferred_categories || [],
          energy_level: formData.energy_level,
          travel_mode: formData.travel_mode,
          constraints: formData.constraints
        },
        itinerary: itinerary,
        is_public: false
      };

      console.log("Saving itinerary with request:", JSON.stringify(saveRequest, null, 2));

      const savedId = await api.saveItinerary(saveRequest, authToken);

      setCurrentSavedId(savedId.id);
      setToast({ message: "Itinerary saved successfully!", type: "success" });

      // Redirect to My Itineraries after successful save
      setTimeout(() => router.push("/my-itineraries"), 1500);
    } catch (error) {
      console.error("Save itinerary error:", error);
      setToast({ message: "Failed to save itinerary", type: "error" });
    } finally {
      setIsSaving(false);
    }
  };

  const selectedCity = cities.find(c => c.id === formData.destination_city_id);

  const formatTime = (timeStr: string) => {
    return new Date(timeStr).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
  };

  return (
    <div className="min-h-screen gradient-bg py-8 px-4 pt-20">
      <div className="max-w-7xl mx-auto">
        {/* Auth Prompt Banner */}
        {!session && (
          <div className="mb-6 glass-card rounded-lg p-4 border border-purple-500/30 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">💡</span>
              <div>
                <p className="text-white font-medium">Sign in to save and share your itinerary</p>
                <p className="text-gray-400 text-sm">Create an account to access your trips from anywhere</p>
              </div>
            </div>
            <button
              onClick={() => signIn("google")}
              className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:opacity-90 transition-opacity whitespace-nowrap"
            >
              Sign In
            </button>
          </div>
        )}

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => router.push("/")}
            className="px-4 py-2 glass-card rounded-lg hover:bg-purple-500/20 transition-colors text-gray-200 hover:text-white"
          >
            ← Back to Home
          </button>
          <h1 className="text-3xl md:text-4xl font-bold gradient-text">
            🏙️ Single City Planner
          </h1>
          <div className="w-24"></div> {/* Spacer for centering */}
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center mb-8 gap-4">
          <div className={`flex items-center gap-2 ${currentStep === "select-city" ? "opacity-100" : "opacity-50"}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              currentStep === "select-city" ? "bg-gradient-to-r from-purple-500 to-pink-500" : "bg-gray-600"
            }`}>
              1
            </div>
            <span className="hidden md:inline text-white">Select City</span>
          </div>
          <div className="w-12 h-0.5 bg-gray-600"></div>
          <div className={`flex items-center gap-2 ${currentStep === "preferences" ? "opacity-100" : "opacity-50"}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              currentStep === "preferences" ? "bg-gradient-to-r from-purple-500 to-pink-500" : "bg-gray-600"
            }`}>
              2
            </div>
            <span className="hidden md:inline text-white">Preferences</span>
          </div>
          <div className="w-12 h-0.5 bg-gray-600"></div>
          <div className={`flex items-center gap-2 ${currentStep === "result" ? "opacity-100" : "opacity-50"}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              currentStep === "result" ? "bg-gradient-to-r from-purple-500 to-pink-500" : "bg-gray-600"
            }`}>
              3
            </div>
            <span className="hidden md:inline text-white">Your Itinerary</span>
          </div>
        </div>

        {/* Step 1: City Selection */}
        {currentStep === "select-city" && (
          <div className="h-[680px]">
            <WorldMapSelector
              cities={cities}
              selectedCities={formData.destination_city_id ? [formData.destination_city_id] : []}
              onCitySelect={handleCitySelect}
              onConfirm={handleCityConfirm}
              onDeselect={handleCityDeselect}
              multiSelect={false}
              title="Choose Your Destination"
            />
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <LoadingProgress cityName={selectedCity?.name} />
        )}

        {/* Step 2: Preferences Form */}
        {currentStep === "preferences" && !loading && (
          <div className="glass-card rounded-2xl p-8">
            <div className="mb-6">
              <h2 className="text-2xl font-bold gradient-text mb-2">
                Plan Your Trip to {selectedCity?.name}
              </h2>
              <p className="text-gray-300">
                📍 {selectedCity?.country} • {selectedCity?.default_currency}
              </p>
              <button
                onClick={() => setCurrentStep("select-city")}
                className="text-purple-400 hover:text-purple-300 text-sm mt-2"
              >
                ← Change destination
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Trip Dates */}
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Start Date
                  </label>
                  <input
                    type="date"
                    required
                    className="w-full px-4 py-2 bg-gray-800/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:border-purple-500"
                    value={formData.start_date || ""}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    End Date
                  </label>
                  <input
                    type="date"
                    required
                    className="w-full px-4 py-2 bg-gray-800/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:border-purple-500"
                    value={formData.end_date || ""}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  />
                </div>
              </div>

              {/* Trip Type */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Trip Type
                </label>
                <select
                  className="w-full px-4 py-2 bg-gray-800/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  value={formData.trip_type}
                  onChange={(e) => setFormData({ ...formData, trip_type: e.target.value as any })}
                >
                  <option value="day_trip">Day Trip</option>
                  <option value="weekend">Weekend Getaway</option>
                  <option value="one_week">One Week</option>
                  <option value="long">Extended Stay</option>
                </select>
              </div>

              {/* Budget */}
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Budget Level
                  </label>
                  <select
                    className="w-full px-4 py-2 bg-gray-800/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:border-purple-500"
                    value={formData.budget_level}
                    onChange={(e) => setFormData({ ...formData, budget_level: e.target.value as any })}
                  >
                    <option value="low">Budget-Friendly</option>
                    <option value="medium">Moderate</option>
                    <option value="high">Luxury</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Budget per Day ({selectedCity?.default_currency})
                  </label>
                  <input
                    type="number"
                    placeholder="Optional"
                    className="w-full px-4 py-2 bg-gray-800/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:border-purple-500"
                    value={formData.budget_per_day || ""}
                    onChange={(e) => setFormData({ ...formData, budget_per_day: Number(e.target.value) })}
                  />
                </div>
              </div>

              {/* Energy Level & Travel Mode */}
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Energy Level
                  </label>
                  <select
                    className="w-full px-4 py-2 bg-gray-800/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:border-purple-500"
                    value={formData.energy_level}
                    onChange={(e) => setFormData({ ...formData, energy_level: e.target.value as any })}
                  >
                    <option value="relaxed">Relaxed</option>
                    <option value="moderate">Moderate</option>
                    <option value="active">Active</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Travel Mode
                  </label>
                  <select
                    className="w-full px-4 py-2 bg-gray-800/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:border-purple-500"
                    value={formData.travel_mode}
                    onChange={(e) => setFormData({ ...formData, travel_mode: e.target.value as any })}
                  >
                    <option value="walking">Walking</option>
                    <option value="public_transport">Public Transport</option>
                    <option value="taxi">Taxi/Rideshare</option>
                    <option value="self_drive">Self Drive</option>
                    <option value="mixed">Mixed</option>
                  </select>
                </div>
              </div>

              {/* Categories */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Preferred Categories
                </label>
                <div className="flex flex-wrap gap-2">
                  {CATEGORIES.map((category) => (
                    <button
                      key={category}
                      type="button"
                      onClick={() => toggleCategory(category)}
                      className={`px-4 py-2 rounded-lg transition-all ${
                        formData.preferred_categories?.includes(category)
                          ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                          : "bg-gray-800/50 text-gray-300 hover:bg-gray-700/50"
                      }`}
                    >
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {loading ? "Generating Itinerary..." : "Generate Itinerary"}
              </button>
            </form>
          </div>
        )}

        {/* Step 3: Results */}
        {currentStep === "result" && itinerary && (
          <div className="space-y-6">
            {/* Header with Save Button */}
            <div className="glass-card rounded-2xl p-6 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold gradient-text">
                  Your {selectedCity?.name} Itinerary
                </h2>
                <p className="text-gray-300 mt-1">
                  {itinerary.days.length} days • {selectedCity?.default_currency} {itinerary.summary.total_cost.toFixed(0)} total
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setCurrentStep("preferences");
                    setItinerary(null);
                  }}
                  className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  Edit Plan
                </button>
                <button
                  onClick={handleShareItinerary}
                  disabled={isSharing}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {isSharing ? "Sharing..." : "🔗 Share"}
                </button>
                <button
                  onClick={handleSaveItinerary}
                  disabled={isSaving}
                  className="px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  {isSaving ? "Saving..." : "Save Itinerary"}
                </button>
              </div>
            </div>

            {/* AI Narrative */}
            {itinerary.narrative?.narrative_text && (
              <div className="glass-card rounded-2xl p-6">
                <h3 className="text-xl font-bold text-white mb-3">✨ AI Travel Guide</h3>
                <p className="text-gray-300 leading-relaxed whitespace-pre-line">
                  {itinerary.narrative.narrative_text}
                </p>
              </div>
            )}

            {/* Refine Itinerary */}
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-lg font-bold text-white mb-1">🔧 Refine with AI</h3>
              <p className="text-gray-400 text-sm mb-4">Tell the AI what to change — it will update your itinerary.</p>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={refineMessage}
                  onChange={(e) => setRefineMessage(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !isRefining && handleRefine()}
                  placeholder='e.g. "Replace Day 2 museum with nightlife" or "Add a food experience on Day 1"'
                  className="flex-1 bg-gray-800/60 border border-gray-600 text-white rounded-lg px-4 py-3 text-sm placeholder-gray-500 focus:outline-none focus:border-purple-500"
                  disabled={isRefining}
                />
                <button
                  onClick={handleRefine}
                  disabled={isRefining || !refineMessage.trim()}
                  className="px-5 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-40 text-sm whitespace-nowrap"
                >
                  {isRefining ? "Refining..." : "Apply"}
                </button>
              </div>
              {refineResult && (
                <div className={`mt-3 text-sm px-4 py-3 rounded-lg ${refineResult.startsWith("Could not") || refineResult.startsWith("Request failed") ? "bg-red-900/30 text-red-300" : "bg-purple-900/30 text-purple-200"}`}>
                  {refineResult}
                </div>
              )}
              {refineAlternatives && refineAlternatives.length > 0 && (
                <div className="mt-3">
                  <p className="text-gray-400 text-xs mb-2">Other options from Google Places:</p>
                  <div className="space-y-2">
                    {refineAlternatives.map((alt) => (
                      <div key={alt.place_id} className="flex items-center justify-between bg-gray-800/40 rounded-lg px-4 py-2.5">
                        <div>
                          <span className="text-white text-sm font-medium">{alt.name}</span>
                          <span className="text-gray-400 text-xs ml-2">{alt.address}</span>
                        </div>
                        <div className="flex items-center gap-3 shrink-0 ml-4">
                          <span className="text-yellow-400 text-xs">⭐ {alt.rating}</span>
                          {alt.price_label && <span className="text-gray-400 text-xs">{alt.price_label}</span>}
                          <a
                            href={`https://www.google.com/maps/place/?q=place_id:${alt.place_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                          >
                            View →
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex flex-wrap gap-2 mt-3">
                {["Replace Day 1 with more food", "Add nightlife on last day", "Remove most expensive activity", "Swap Day 2 for outdoor activities"].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setRefineMessage(suggestion)}
                    className="text-xs px-3 py-1.5 bg-gray-700/60 text-gray-300 rounded-full hover:bg-gray-600/60 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>

            {/* Daily Itinerary — Immersive Two-Panel Layout */}
            <div className="glass-card rounded-2xl overflow-hidden flex" style={{ minHeight: "600px" }}>

              {/* Left Sidebar — Day List */}
              <div className="w-52 shrink-0 border-r border-white/10 flex flex-col overflow-y-auto">
                <div className="px-4 py-3 border-b border-white/10">
                  <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">Your Trip</p>
                  <p className="text-sm font-bold text-white mt-0.5">{itinerary.days.length} Days</p>
                </div>
                <div className="flex-1">
                  {itinerary.days.map((day, dayIndex) => {
                    const date = new Date(day.date);
                    const isActive = activeDayIndex === dayIndex;
                    const dayLabel = date.toLocaleDateString("en-US", { weekday: "short" });
                    const dateLabel = date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
                    const categoryIcons: Record<string, string> = {
                      food: "🍽️", culture: "🏛️", nightlife: "🌙", nature: "🌿",
                      shopping: "🛍️", adventure: "⛰️", beaches: "🏖️",
                    };
                    const topCategories = [...new Set(day.blocks.map(b => b.activity.category))].slice(0, 3);

                    return (
                      <button
                        key={dayIndex}
                        onClick={() => setActiveDayIndex(dayIndex)}
                        className={`relative w-full text-left px-4 py-4 transition-all duration-200 border-b border-white/5 ${
                          isActive
                            ? "bg-purple-600/20 text-white"
                            : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
                        }`}
                      >
                        {isActive && (
                          <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-gradient-to-b from-purple-500 to-pink-500" />
                        )}
                        <div className="flex items-center justify-between mb-1">
                          <span className={`text-xs font-bold uppercase tracking-wider ${isActive ? "text-purple-400" : "text-gray-600"}`}>
                            Day {dayIndex + 1}
                          </span>
                          <span className={`text-xs ${isActive ? "text-purple-300" : "text-gray-600"}`}>
                            {selectedCity?.default_currency}{day.total_cost.toFixed(0)}
                          </span>
                        </div>
                        <div className="text-sm font-semibold mb-1">{dayLabel}, {dateLabel}</div>
                        <div className="flex gap-0.5 text-sm">
                          {topCategories.map(cat => (
                            <span key={cat} title={cat}>{categoryIcons[cat] ?? "📍"}</span>
                          ))}
                          <span className="text-xs text-gray-600 ml-1 self-center">{day.blocks.length} stops</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Right Panel — Active Day Content */}
              {(() => {
                const day = itinerary.days[activeDayIndex];
                if (!day) return null;
                const date = new Date(day.date);
                const travelMode = formData.travel_mode || "mixed";
                const modeIcon: Record<string, string> = {
                  walking: "🚶", public_transport: "🚌", taxi: "🚕", self_drive: "🚗", mixed: "🗺️",
                };
                const modeLabel: Record<string, string> = {
                  walking: "walk", public_transport: "transit", taxi: "taxi", self_drive: "drive", mixed: "travel",
                };
                const gmapsTravelMode = travelMode === "public_transport" ? "transit"
                  : travelMode === "walking" ? "walking" : "driving";

                return (
                  <div className="flex-1 overflow-y-auto">
                    {/* Day header */}
                    <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-bold text-white">
                          Day {activeDayIndex + 1} — {date.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
                        </h3>
                        <p className="text-sm text-gray-400 mt-0.5">
                          {day.blocks.length} activities · {Math.round(day.total_duration_minutes / 60)}h planned
                        </p>
                      </div>
                      <span className="text-purple-300 font-semibold text-sm">
                        {selectedCity?.default_currency} {day.total_cost.toFixed(0)}
                      </span>
                    </div>

                    <div className="p-6">
                      {/* Map */}
                      <div className="mb-6 rounded-xl overflow-hidden mx-auto" style={{ maxWidth: "75%" }}>
                        <GoogleItineraryMap key={activeDayIndex} activities={day.blocks.map(b => b.activity)} />
                      </div>

                      {/* Timeline */}
                      <div className="space-y-1">
                        {day.blocks.map((block, blockIndex) => {
                          const prevBlock = blockIndex > 0 ? day.blocks[blockIndex - 1] : null;
                          const mapsUrl = prevBlock
                            ? `https://www.google.com/maps/dir/?api=1&origin=${prevBlock.activity.coordinates.latitude},${prevBlock.activity.coordinates.longitude}&destination=${block.activity.coordinates.latitude},${block.activity.coordinates.longitude}&travelmode=${gmapsTravelMode}`
                            : null;
                          const categoryColors: Record<string, string> = {
                            food: "bg-emerald-500", culture: "bg-purple-500", nightlife: "bg-pink-500",
                            nature: "bg-green-500", shopping: "bg-amber-500", adventure: "bg-red-500", beaches: "bg-cyan-500",
                          };
                          const dotColor = categoryColors[block.activity.category] ?? "bg-indigo-500";

                          return (
                            <div key={blockIndex}>
                              {/* Travel connector */}
                              {block.travel_time_from_previous && block.travel_time_from_previous > 0 && (
                                <div className="flex items-center gap-3 pl-[52px] py-1">
                                  <div className="w-px h-5 bg-purple-500/30" />
                                  <span className="text-xs text-gray-500 flex items-center gap-1.5">
                                    {modeIcon[travelMode]} {block.travel_time_from_previous} min {modeLabel[travelMode]}
                                    {mapsUrl && (
                                      <a href={mapsUrl} target="_blank" rel="noopener noreferrer"
                                        onClick={e => e.stopPropagation()}
                                        className="text-blue-400 hover:text-blue-300">
                                        · Directions ↗
                                      </a>
                                    )}
                                  </span>
                                </div>
                              )}

                              {/* Activity card */}
                              <div
                                className="flex items-start gap-4 p-4 rounded-xl hover:bg-white/5 transition-colors cursor-pointer group"
                                onClick={() => setSelectedActivity(block.activity)}
                              >
                                {/* Timeline dot + time */}
                                <div className="flex flex-col items-center gap-1 shrink-0 w-12">
                                  <div className={`w-3 h-3 rounded-full ${dotColor} ring-2 ring-gray-900 mt-1`} />
                                  <span className="text-purple-400 font-mono text-xs">
                                    {formatTime(block.start_time)}
                                  </span>
                                </div>

                                {/* Content */}
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-start justify-between gap-2">
                                    <h4 className="font-semibold text-white group-hover:text-purple-200 transition-colors">
                                      {block.activity.name}
                                    </h4>
                                    <span className="text-purple-300 font-medium text-sm shrink-0">
                                      {selectedCity?.default_currency} {block.activity.cost.toFixed(0)}
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                                    <span className={`text-xs px-2 py-0.5 rounded-full text-white/90 ${dotColor}/30 border border-white/10`}>
                                      {block.activity.category}
                                    </span>
                                    <span className="text-xs text-gray-500">⏱ {block.activity.duration} min</span>
                                    <span className="text-xs text-yellow-400">⭐ {block.activity.rating.toFixed(1)}</span>
                                  </div>
                                  {block.activity.description && (
                                    <p className="text-gray-500 text-xs mt-1 truncate">{block.activity.description}</p>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {/* Toast */}
        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}

        {/* Activity Modal */}
        {selectedActivity && (
          <ActivityModal
            activity={selectedActivity}
            onClose={() => setSelectedActivity(null)}
          />
        )}
      </div>
    </div>
  );
}
