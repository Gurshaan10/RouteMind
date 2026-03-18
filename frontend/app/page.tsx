"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LandingPage() {
  const router = useRouter();
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  return (
    <div className="min-h-screen gradient-bg pt-24 pb-8 px-2 md:px-4">
      <div className="max-w-6xl mx-auto">
        {/* Hero Section */}
        <div className="text-center mb-12 md:mb-16 animate-fade-in">
          <div className="inline-block mb-4">
            <div className="text-5xl md:text-6xl mb-3 animate-float">🧭</div>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold gradient-text mb-4">
            RouteMind
          </h1>
          <p className="text-xl md:text-3xl text-white font-semibold drop-shadow-lg mb-3">
            AI-Powered Travel Itinerary Planner
          </p>
          <p className="text-base md:text-lg text-white/90 max-w-2xl mx-auto">
            Let our AI craft the perfect itinerary for your next adventure.
            Optimized routes, personalized recommendations, and seamless planning.
          </p>

          {/* Quick Access Links */}
          <div className="flex items-center justify-center gap-4 mt-6">
            <a
              href="/my-itineraries"
              className="glass px-6 py-3 rounded-full font-semibold text-white hover:bg-white/40 transition-all flex items-center gap-2 hover-lift shadow-lg"
            >
              📚 My Itineraries
            </a>
          </div>
        </div>

        {/* Main Choice Cards */}
        <div className="glass-strong rounded-3xl shadow-2xl p-6 md:p-10 animate-scale-in border border-white/30 mb-8">
          <h2 className="text-2xl md:text-3xl font-bold gradient-text mb-3 text-center">
            What are you planning today?
          </h2>
          <p className="text-center text-gray-600 mb-8 font-medium">
            Choose your travel style to get started
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
            {/* Single City Card */}
            <button
              onClick={() => router.push("/plan/single-city")}
              onMouseEnter={() => setHoveredCard("single")}
              onMouseLeave={() => setHoveredCard(null)}
              className="group relative glass-strong rounded-2xl p-8 border-2 border-white/30 hover:border-primary-400 transition-all hover-lift shadow-lg hover:shadow-2xl text-left"
            >
              <div className="absolute top-4 right-4 text-5xl group-hover:scale-110 transition-transform">
                🏙️
              </div>

              <div className="mb-4">
                <h3 className="text-2xl md:text-3xl font-bold gradient-text mb-2">
                  Single City
                </h3>
                <p className="text-gray-600 font-medium">
                  Deep dive into one destination
                </p>
              </div>

              <div className="space-y-3 mb-6">
                <div className="flex items-start gap-3">
                  <span className="text-primary-500 font-bold">✓</span>
                  <span className="text-gray-700 text-sm">
                    Perfect for weekend getaways or focused exploration
                  </span>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-primary-500 font-bold">✓</span>
                  <span className="text-gray-700 text-sm">
                    Optimized daily schedules with time for everything
                  </span>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-primary-500 font-bold">✓</span>
                  <span className="text-gray-700 text-sm">
                    Detailed activity recommendations and routes
                  </span>
                </div>
              </div>

              <div
                className={`px-4 py-2 rounded-xl font-semibold text-sm text-center transition-all ${
                  hoveredCard === "single"
                    ? "bg-gradient-to-r from-primary-600 to-accent-600 text-white shadow-glow"
                    : "bg-gradient-to-r from-primary-100 to-accent-100 text-primary-700"
                }`}
              >
                Plan Single City →
              </div>
            </button>

            {/* Multi-City Card */}
            <button
              onClick={() => router.push("/plan/multi-city")}
              onMouseEnter={() => setHoveredCard("multi")}
              onMouseLeave={() => setHoveredCard(null)}
              className="group relative glass-strong rounded-2xl p-8 border-2 border-white/30 hover:border-accent-400 transition-all hover-lift shadow-lg hover:shadow-2xl text-left"
            >
              <div className="absolute top-4 right-4 text-5xl group-hover:scale-110 transition-transform">
                🗺️
              </div>

              <div className="mb-4">
                <h3 className="text-2xl md:text-3xl font-bold gradient-text mb-2">
                  Multi-City
                </h3>
                <p className="text-gray-600 font-medium">
                  Epic adventures across destinations
                </p>
              </div>

              <div className="space-y-3 mb-6">
                <div className="flex items-start gap-3">
                  <span className="text-accent-500 font-bold">✓</span>
                  <span className="text-gray-700 text-sm">
                    Visit 2-5 cities in one seamless trip
                  </span>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-accent-500 font-bold">✓</span>
                  <span className="text-gray-700 text-sm">
                    Smart allocation of days across destinations
                  </span>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-accent-500 font-bold">✓</span>
                  <span className="text-gray-700 text-sm">
                    Individual itineraries for each city
                  </span>
                </div>
              </div>

              <div
                className={`px-4 py-2 rounded-xl font-semibold text-sm text-center transition-all ${
                  hoveredCard === "multi"
                    ? "bg-gradient-to-r from-accent-600 to-primary-600 text-white shadow-glow"
                    : "bg-gradient-to-r from-accent-100 to-primary-100 text-accent-700"
                }`}
              >
                Plan Multi-City →
              </div>
            </button>
          </div>
        </div>

        {/* Features Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="glass rounded-2xl p-6 border border-white/30 text-center hover-lift transition-all">
            <div className="text-4xl mb-3">🧠</div>
            <h3 className="text-lg font-bold text-white mb-2">
              Semantic RAG Retrieval
            </h3>
            <p className="text-sm text-gray-300">
              pgvector embeddings rank activities by semantic similarity to your preferences — not just keyword filters
            </p>
          </div>

          <div className="glass rounded-2xl p-6 border border-white/30 text-center hover-lift transition-all">
            <div className="text-4xl mb-3">⚙️</div>
            <h3 className="text-lg font-bold text-white mb-2">
              Constraint Optimizer
            </h3>
            <p className="text-sm text-gray-300">
              Greedy scheduling with travel-time feasibility checks builds routes that actually make geographic sense
            </p>
          </div>

          <div className="glass rounded-2xl p-6 border border-white/30 text-center hover-lift transition-all">
            <div className="text-4xl mb-3">🔄</div>
            <h3 className="text-lg font-bold text-white mb-2">
              LLM Refinement Loop
            </h3>
            <p className="text-sm text-gray-300">
              Natural language edits are parsed by an LLM intent classifier, then re-planned deterministically by the optimizer
            </p>
          </div>
        </div>

        {/* Stats Section */}
        <div className="glass-strong rounded-2xl p-8 border border-white/30 text-center">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div>
              <div className="text-3xl md:text-4xl font-bold gradient-text mb-1">
                70+
              </div>
              <div className="text-sm text-gray-600 font-medium">
                Global Cities
              </div>
            </div>
            <div>
              <div className="text-3xl md:text-4xl font-bold gradient-text mb-1">
                1,500+
              </div>
              <div className="text-sm text-gray-600 font-medium">
                Curated Activities
              </div>
            </div>
            <div>
              <div className="text-3xl md:text-4xl font-bold gradient-text mb-1">
                Smart
              </div>
              <div className="text-sm text-gray-600 font-medium">
                AI Optimization
              </div>
            </div>
            <div>
              <div className="text-3xl md:text-4xl font-bold gradient-text mb-1">
                Free
              </div>
              <div className="text-sm text-gray-600 font-medium">
                Always & Forever
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
