"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  ZoomableGroup,
} from "react-simple-maps";

interface City {
  id: number;
  name: string;
  country: string;
  time_zone: string;
  default_currency: string;
  latitude?: number;
  longitude?: number;
}

interface WorldMapSelectorProps {
  cities: City[];
  selectedCities: number[];
  onCitySelect: (cityId: number) => void;
  /** Single-city only: called when user clicks "Plan this trip →" in the confirmation banner */
  onConfirm?: (cityId: number) => void;
  /** Single-city only: called when user deselects a city */
  onDeselect?: () => void;
  multiSelect?: boolean;
  title?: string;
}

// Approximate coordinates for major cities (we'll use these until real lat/lng is in DB)
const CITY_COORDINATES: { [key: string]: [number, number] } = {
  // USA
  "New York": [-74.006, 40.7128],
  "Los Angeles": [-118.2437, 34.0522],
  "Chicago": [-87.6298, 41.8781],
  "Houston": [-95.3698, 29.7604],
  "Phoenix": [-112.074, 33.4484],
  "Philadelphia": [-75.1652, 39.9526],
  "San Antonio": [-98.4936, 29.4241],
  "San Diego": [-117.1611, 32.7157],
  "Dallas": [-96.797, 32.7767],
  "San Jose": [-121.8863, 37.3382],
  "Austin": [-97.7431, 30.2672],
  "Jacksonville": [-81.6557, 30.3322],
  "Fort Worth": [-97.3308, 32.7555],
  "Columbus": [-82.9988, 39.9612],
  "San Francisco": [-122.4194, 37.7749],
  "Charlotte": [-80.8431, 35.2271],
  "Indianapolis": [-86.1581, 39.7684],
  "Seattle": [-122.3321, 47.6062],
  "Denver": [-104.9903, 39.7392],
  "Boston": [-71.0589, 42.3601],

  // UK
  "London": [-0.1276, 51.5074],
  "Manchester": [-2.2426, 53.4808],
  "Birmingham": [-1.8904, 52.4862],
  "Leeds": [-1.5491, 53.8008],
  "Glasgow": [-4.2518, 55.8642],
  "Edinburgh": [-3.1883, 55.9533],
  "Liverpool": [-2.9916, 53.4084],
  "Bristol": [-2.5879, 51.4545],
  "Cardiff": [-3.1791, 51.4816],
  "Belfast": [-5.9301, 54.5973],

  // Europe
  "Paris": [2.3522, 48.8566],
  "Berlin": [13.405, 52.52],
  "Madrid": [-3.7038, 40.4168],
  "Rome": [12.4964, 41.9028],
  "Barcelona": [2.1734, 41.3851],
  "Amsterdam": [4.9041, 52.3676],
  "Milan": [9.19, 45.4642],
  "Prague": [14.4378, 50.0755],
  "Vienna": [16.3738, 48.2082],
  "Munich": [11.582, 48.1351],
  "Lisbon": [-9.1393, 38.7223],
  "Copenhagen": [12.5683, 55.6761],
  "Stockholm": [18.0686, 59.3293],
  "Brussels": [4.3517, 50.8503],
  "Zurich": [8.541, 47.3769],
  "Athens": [23.7275, 37.9838],
  "Dublin": [-6.2603, 53.3498],
  "Hamburg": [9.9937, 53.5511],
  "Warsaw": [21.0122, 52.2297],
  "Budapest": [19.0402, 47.4979],

  // Asia
  "Tokyo": [139.6917, 35.6895],
  "Seoul": [126.978, 37.5665],
  "Singapore": [103.8198, 1.3521],
  "Hong Kong": [114.1694, 22.3193],
  "Bangkok": [100.5018, 13.7563],
  "Dubai": [55.2708, 25.2048],
  "Kuala Lumpur": [101.6869, 3.139],
  "Shanghai": [121.4737, 31.2304],
  "Beijing": [116.4074, 39.9042],
  "Mumbai": [72.8777, 19.076],
  "Delhi": [77.1025, 28.7041],
  "Bangalore": [77.5946, 12.9716],
  "Taipei": [121.5654, 25.033],
  "Osaka": [135.5023, 34.6937],
  "Manila": [120.9842, 14.5995],
  "Jakarta": [106.8456, -6.2088],
  "Hanoi": [105.8342, 21.0285],
  "Ho Chi Minh City": [106.6297, 10.8231],
  "Phuket": [98.3923, 7.8804],
  "Bali": [115.1889, -8.3405],

  // Other
  "Sydney": [151.2093, -33.8688],
};

// Group cities by continent/region for the list
const REGION_ORDER = ["Americas", "Europe", "Middle East", "Asia", "Oceania"];

const COUNTRY_REGION: Record<string, string> = {
  // Americas
  "United States": "Americas",
  "Canada": "Americas",
  "Mexico": "Americas",
  "Brazil": "Americas",
  "Argentina": "Americas",
  "Colombia": "Americas",
  "Peru": "Americas",
  "Chile": "Americas",
  // Europe
  "United Kingdom": "Europe",
  "France": "Europe",
  "Germany": "Europe",
  "Spain": "Europe",
  "Italy": "Europe",
  "Netherlands": "Europe",
  "Belgium": "Europe",
  "Austria": "Europe",
  "Czech Republic": "Europe",
  "Hungary": "Europe",
  "Poland": "Europe",
  "Portugal": "Europe",
  "Greece": "Europe",
  "Ireland": "Europe",
  "Sweden": "Europe",
  "Denmark": "Europe",
  "Norway": "Europe",
  "Finland": "Europe",
  "Switzerland": "Europe",
  "Romania": "Europe",
  "Croatia": "Europe",
  "Serbia": "Europe",
  // Middle East
  "United Arab Emirates": "Middle East",
  "Saudi Arabia": "Middle East",
  "Qatar": "Middle East",
  "Jordan": "Middle East",
  "Israel": "Middle East",
  "Turkey": "Middle East",
  "Egypt": "Middle East",
  // Asia
  "Japan": "Asia",
  "South Korea": "Asia",
  "China": "Asia",
  "India": "Asia",
  "Singapore": "Asia",
  "Thailand": "Asia",
  "Vietnam": "Asia",
  "Indonesia": "Asia",
  "Philippines": "Asia",
  "Malaysia": "Asia",
  "Taiwan": "Asia",
  "Hong Kong": "Asia",
  // Oceania
  "Australia": "Oceania",
  "New Zealand": "Oceania",
};

function getRegion(country: string): string {
  return COUNTRY_REGION[country] ?? "Other";
}

const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

function editDistance(a: string, b: string): number {
  const m = a.length, n = b.length;
  const dp: number[][] = Array.from({ length: m + 1 }, (_, i) =>
    Array.from({ length: n + 1 }, (_, j) => (i === 0 ? j : j === 0 ? i : 0))
  );
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      dp[i][j] = a[i - 1] === b[j - 1]
        ? dp[i - 1][j - 1]
        : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
  return dp[m][n];
}

export default function WorldMapSelector({
  cities,
  selectedCities,
  onCitySelect,
  onConfirm,
  onDeselect,
  multiSelect = false,
  title = "Select Your Destination",
}: WorldMapSelectorProps) {
  const [hoveredCityId, setHoveredCityId] = useState<number | null>(null);
  const [position, setPosition] = useState({ coordinates: [0, 20] as [number, number], zoom: 1 });
  const [search, setSearch] = useState("");
  // For single-city: the city just clicked, pending confirmation
  const [pendingCity, setPendingCity] = useState<City | null>(null);
  const selectedListItemRef = useRef<HTMLButtonElement | null>(null);
  const listPanelRef = useRef<HTMLDivElement | null>(null);
  const hoveredCityIdRef = useRef<number | null>(null);

  const setHovered = (city: City | null, fromMap = false) => {
    hoveredCityIdRef.current = city?.id ?? null;
    setHoveredCityId(city?.id ?? null);
    // Scroll list to the hovered city only when hover comes from the map
    if (fromMap && city && listPanelRef.current) {
      const el = listPanelRef.current.querySelector<HTMLElement>(`[data-city-id="${city.id}"]`);
      el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  };


  const getCityCoordinates = (city: City): [number, number] => {
    if (city.latitude && city.longitude) {
      return [city.longitude, city.latitude];
    }
    return CITY_COORDINATES[city.name] || [0, 0];
  };

  const handleCityClick = (city: City) => {
    if (onConfirm) {
      // Single-city mode: clicking the already-pending city deselects it
      if (pendingCity?.id === city.id) {
        setPendingCity(null);
        onDeselect?.();
        return;
      }
      onCitySelect(city.id);
      setPendingCity(city);
      const coords = getCityCoordinates(city);
      setPosition({ coordinates: coords, zoom: 3 });
    } else {
      // Multi-city mode: toggle directly
      onCitySelect(city.id);
    }
  };

  const handleConfirm = () => {
    if (pendingCity && onConfirm) {
      onConfirm(pendingCity.id);
    }
  };

  const isCitySelected = (cityId: number) => selectedCities.includes(cityId);

  // Filter cities for the list panel — memoized to keep stable reference
  const filteredCities = useMemo(
    () => cities.filter(
      (c) =>
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.country.toLowerCase().includes(search.toLowerCase())
    ),
    [cities, search]
  );

  // Fuzzy suggestions when no exact match — find cities whose name is "close" to the query
  const fuzzyMatches: City[] = search.length >= 3 && filteredCities.length === 0
    ? cities
        .map((c) => ({ city: c, dist: editDistance(search.toLowerCase(), c.name.toLowerCase()) }))
        .filter(({ dist, city }) => dist <= Math.max(3, Math.floor(city.name.length * 0.4)))
        .sort((a, b) => a.dist - b.dist)
        .slice(0, 3)
        .map(({ city }) => city)
    : [];

  // Group filtered cities by region — stable order, never reordered on hover
  const grouped = useMemo(() => {
    const acc: Record<string, City[]> = {};
    for (const city of filteredCities) {
      const region = getRegion(city.country);
      if (!acc[region]) acc[region] = [];
      acc[region].push(city);
    }
    return acc;
  }, [filteredCities]);

  // Scroll selected city into view in the list
  useEffect(() => {
    if (selectedListItemRef.current) {
      selectedListItemRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [selectedCities]);

  return (
    <div className="w-full h-full flex flex-col">
      {/* Title */}
      <div className="text-center mb-3 px-4">
        <h2 className="text-2xl md:text-3xl font-bold gradient-text mb-1">
          {title}
        </h2>
        <p className="text-gray-300 text-sm">
          {multiSelect
            ? "Click cities on the map or browse the list"
            : "Click a city on the map or search the list"}
        </p>
      </div>

      {/* Main layout: map + sidebar */}
      <div className="flex-1 flex gap-4 min-h-0">
        {/* Globe (left) */}
        <div className="relative flex-1 glass-card rounded-2xl overflow-hidden min-w-0">
          <ComposableMap
            projection="geoMercator"
            projectionConfig={{ scale: 147 }}
            className="w-full h-full"
          >
            <ZoomableGroup
              center={position.coordinates}
              zoom={position.zoom}
              onMoveEnd={({ coordinates, zoom }) => setPosition({ coordinates, zoom })}
            >
              <Geographies geography={geoUrl}>
                {({ geographies }) =>
                  geographies.map((geo) => (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      fill="rgba(99, 102, 241, 0.1)"
                      stroke="rgba(139, 92, 246, 0.3)"
                      strokeWidth={0.5}
                      style={{
                        default: { outline: "none" },
                        hover: { fill: "rgba(139, 92, 246, 0.2)", outline: "none" },
                        pressed: { outline: "none" },
                      }}
                    />
                  ))
                }
              </Geographies>

              {cities.map((city) => {
                const coordinates = getCityCoordinates(city);
                const isSelected = isCitySelected(city.id);
                const isHovered = hoveredCityId === city.id;
                const isPending = pendingCity?.id === city.id;

                return (
                  <Marker
                    key={city.id}
                    coordinates={coordinates}
                    onMouseEnter={() => setHovered(city, true)}
                    onMouseLeave={() => setHovered(null)}
                    onClick={() => handleCityClick(city)}
                    style={{ cursor: "pointer" }}
                  >
                    {(isSelected || isPending) && (
                      <circle r={8} fill="rgba(168, 85, 247, 0.3)" className="animate-pulse" />
                    )}
                    <circle
                      r={isHovered ? 7 : isSelected || isPending ? 5 : 4}
                      fill={isHovered ? "#ffffff" : isSelected || isPending ? "#a855f7" : "#6366f1"}
                      stroke={isHovered ? "#ffffff" : isSelected || isPending ? "#fbbf24" : "#8b5cf6"}
                      strokeWidth={isHovered ? 2 : 1.5}
                      className="transition-all duration-150"
                      style={{
                        filter:
                          isHovered
                            ? "drop-shadow(0 0 10px rgba(255, 255, 255, 0.9))"
                            : isSelected || isPending
                            ? "drop-shadow(0 0 8px rgba(168, 85, 247, 0.8))"
                            : "drop-shadow(0 0 4px rgba(99, 102, 241, 0.5))",
                      }}
                    />
                    {(isSelected || isPending) && (
                      <text
                        textAnchor="middle"
                        y={-10}
                        style={{
                          fontSize: "12px",
                          fill: "#fbbf24",
                          filter: "drop-shadow(0 0 2px rgba(0,0,0,0.8))",
                        }}
                      >
                        ✓
                      </text>
                    )}
                  </Marker>
                );
              })}
            </ZoomableGroup>
          </ComposableMap>

          {/* Hover Tooltip (non-blocking) */}
          {hoveredCityId && !pendingCity && (() => {
            const hc = cities.find(c => c.id === hoveredCityId);
            return hc ? (
              <div className="absolute top-3 left-3 glass-card px-3 py-2 rounded-lg z-10 pointer-events-none animate-fade-in">
                <p className="text-white font-semibold text-sm">{hc.name}</p>
                <p className="text-purple-300 text-xs">{hc.country}</p>
              </div>
            ) : null;
          })()}

          {/* Single-city confirmation banner */}
          {pendingCity && onConfirm && (
            <div className="absolute bottom-0 left-0 right-0 z-20 animate-fade-in">
              <div className="m-3 glass-card rounded-xl border border-purple-500/40 p-4 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0">
                    <span className="text-white text-lg">📍</span>
                  </div>
                  <div className="min-w-0">
                    <p className="text-white font-bold truncate">{pendingCity.name}</p>
                    <p className="text-purple-300 text-xs">{pendingCity.country} · {pendingCity.default_currency}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => { setPendingCity(null); onDeselect?.(); }}
                    className="px-3 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                  >
                    Change
                  </button>
                  <button
                    onClick={handleConfirm}
                    className="px-5 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold text-sm hover:opacity-90 transition-opacity flex items-center gap-1"
                  >
                    Plan this trip →
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Map Controls */}
          <div className="absolute bottom-4 right-4 flex flex-col gap-2" style={{ bottom: pendingCity ? "5rem" : "1rem" }}>
            <button
              onClick={() => setPosition({ ...position, zoom: Math.min(position.zoom * 1.5, 8) })}
              className="w-9 h-9 glass-card rounded-lg flex items-center justify-center hover:bg-purple-500/20 transition-colors text-white text-xl"
              title="Zoom In"
            >
              +
            </button>
            <button
              onClick={() => setPosition({ ...position, zoom: Math.max(position.zoom / 1.5, 1) })}
              className="w-9 h-9 glass-card rounded-lg flex items-center justify-center hover:bg-purple-500/20 transition-colors text-white text-xl"
              title="Zoom Out"
            >
              −
            </button>
            <button
              onClick={() => setPosition({ coordinates: [0, 20], zoom: 1 })}
              className="w-9 h-9 glass-card rounded-lg flex items-center justify-center hover:bg-purple-500/20 transition-colors text-lg"
              title="Reset View"
            >
              🌍
            </button>
          </div>
        </div>

        {/* City List Panel (right) */}
        <div className="w-64 flex-shrink-0 glass-card rounded-2xl flex flex-col overflow-hidden">
          {/* Search */}
          <div className="p-3 border-b border-white/10">
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
              <input
                type="text"
                placeholder="Search cities..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-8 pr-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm placeholder-gray-400 focus:outline-none focus:border-purple-500/50"
              />
            </div>
            {selectedCities.length > 0 && !pendingCity && (
              <p className="text-purple-400 text-xs mt-2 text-center">
                ✓ {selectedCities.length} {selectedCities.length === 1 ? "city" : "cities"} selected
              </p>
            )}
            {pendingCity && (
              <p className="text-yellow-400 text-xs mt-2 text-center font-medium">
                📍 {pendingCity.name} selected
              </p>
            )}
          </div>

          {/* Grouped city list */}
          <div ref={listPanelRef} className="flex-1 overflow-y-auto">
            {REGION_ORDER.filter((r) => grouped[r]?.length > 0).map((region) => (
              <div key={region}>
                <div className="px-3 py-1.5 text-xs font-semibold text-purple-400 uppercase tracking-wider bg-[#1e1330] sticky top-0 z-10">
                  {region}
                </div>
                {grouped[region].map((city) => {
                  const isSelected = isCitySelected(city.id);
                  const isHovered = hoveredCityId === city.id;
                  const isPending = pendingCity?.id === city.id;
                  return (
                    <button
                      key={city.id}
                      ref={isSelected || isPending ? selectedListItemRef : null}
                      data-city-id={city.id}
                      onClick={() => handleCityClick(city)}
                      onMouseEnter={() => setHovered(city)}
                      onMouseLeave={() => setHovered(null)}
                      className={`w-full text-left px-3 py-2 flex items-center justify-between transition-all ${
                        isPending
                          ? "bg-yellow-500/10 border-l-2 border-yellow-400"
                          : isSelected
                          ? "bg-purple-500/20 border-l-2 border-purple-400"
                          : isHovered
                          ? "bg-white/10"
                          : "hover:bg-white/5"
                      }`}
                    >
                      <div className="min-w-0">
                        <p className={`text-sm font-medium truncate ${isPending ? "text-yellow-300" : isSelected ? "text-purple-300" : "text-white"}`}>
                          {city.name}
                        </p>
                        <p className="text-xs text-gray-400 truncate">{city.country}</p>
                      </div>
                      {(isSelected || isPending) && (
                        <span className={`text-xs ml-2 flex-shrink-0 ${isPending ? "text-yellow-400" : "text-yellow-400"}`}>✓</span>
                      )}
                    </button>
                  );
                })}
              </div>
            ))}
            {filteredCities.length === 0 && search.length > 0 && (
              <div className="px-4 py-6 text-center">
                {fuzzyMatches.length > 0 ? (
                  <>
                    <p className="text-gray-400 text-xs mb-3">Did you mean…</p>
                    {fuzzyMatches.map((city) => (
                      <button
                        key={city.id}
                        onClick={() => handleCityClick(city)}
                        onMouseEnter={() => setHovered(city)}
                        onMouseLeave={() => setHovered(null)}
                        className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/10 transition-all mb-1"
                      >
                        <p className="text-white font-medium text-sm">{city.name}</p>
                        <p className="text-gray-400 text-xs">{city.country}</p>
                      </button>
                    ))}
                  </>
                ) : (
                  <>
                    <div className="text-3xl mb-3">🌍</div>
                    <p className="text-white font-semibold text-sm mb-1">
                      "{search}" not available yet
                    </p>
                    <p className="text-gray-400 text-xs leading-relaxed">
                      We're constantly expanding our database. Check back soon!
                    </p>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
