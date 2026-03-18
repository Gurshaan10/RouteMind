"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { GoogleMap, Marker, InfoWindow, Polyline } from "@react-google-maps/api";

interface Activity {
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
}

interface GoogleItineraryMapProps {
  activities: Activity[];
}

const mapContainerStyle = {
  width: "100%",
  height: "400px",
  borderRadius: "1rem",
};

const mapOptions = {
  disableDefaultUI: false,
  zoomControl: true,
  mapTypeControl: false,
  scaleControl: true,
  streetViewControl: true,
  rotateControl: false,
  fullscreenControl: true,
  styles: [
    {
      featureType: "poi",
      elementType: "labels",
      stylers: [{ visibility: "off" }],
    },
  ],
};

// Category colors matching the UI theme
const getCategoryColor = (category: string): string => {
  const colors: { [key: string]: string } = {
    food: "#10b981",      // emerald
    culture: "#8b5cf6",   // purple
    nightlife: "#ec4899", // pink
    nature: "#22c55e",    // green
    shopping: "#f59e0b",  // amber
    adventure: "#ef4444", // red
    beaches: "#06b6d4",   // cyan
  };
  return colors[category.toLowerCase()] || "#6366f1"; // default indigo
};

const getMarkerLabel = (index: number): google.maps.MarkerLabel => {
  return {
    text: (index + 1).toString(),
    color: "white",
    fontSize: "14px",
    fontWeight: "bold",
  };
};

export default function GoogleItineraryMap({ activities }: GoogleItineraryMapProps) {
  const [selectedActivity, setSelectedActivity] = useState<{ activity: Activity; index: number } | null>(null);
  const [center, setCenter] = useState({ lat: 0, lng: 0 });
  const [zoom, setZoom] = useState(13);
  const mapRef = useRef<google.maps.Map | null>(null);

  const onMapLoad = useCallback((map: google.maps.Map) => {
    mapRef.current = map;
    // Trigger resize at multiple intervals to handle accordion/panel expand animations
    setTimeout(() => google.maps.event.trigger(map, "resize"), 100);
    setTimeout(() => google.maps.event.trigger(map, "resize"), 400);
    setTimeout(() => google.maps.event.trigger(map, "resize"), 800);
  }, []);

  // Re-trigger resize whenever activities change (day switching)
  useEffect(() => {
    if (mapRef.current) {
      setTimeout(() => google.maps.event.trigger(mapRef.current!, "resize"), 100);
    }
  }, [activities]);

  // Filter out activities with invalid (0,0) coordinates
  const validActivities = activities.filter(
    (act) => act.coordinates.latitude !== 0 || act.coordinates.longitude !== 0
  );

  useEffect(() => {
    if (validActivities.length > 0) {
      // Calculate center from all activities
      const avgLat = validActivities.reduce((sum, act) => sum + act.coordinates.latitude, 0) / validActivities.length;
      const avgLng = validActivities.reduce((sum, act) => sum + act.coordinates.longitude, 0) / validActivities.length;
      setCenter({ lat: avgLat, lng: avgLng });

      // Calculate appropriate zoom level based on spread
      const latitudes = validActivities.map(a => a.coordinates.latitude);
      const longitudes = validActivities.map(a => a.coordinates.longitude);
      const latSpread = Math.max(...latitudes) - Math.min(...latitudes);
      const lngSpread = Math.max(...longitudes) - Math.min(...longitudes);
      const maxSpread = Math.max(latSpread, lngSpread);

      // Determine zoom level (rough approximation)
      if (maxSpread > 0.5) setZoom(11);
      else if (maxSpread > 0.2) setZoom(12);
      else if (maxSpread > 0.1) setZoom(13);
      else setZoom(14);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activities]);

  if (validActivities.length === 0) {
    return (
      <div className="w-full h-96 bg-gray-50 rounded-lg flex items-center justify-center border-2 border-gray-200">
        <p className="text-gray-500 font-medium">No activities to display</p>
      </div>
    );
  }

  // Create path for polyline (route between activities in order)
  const path = validActivities.map((activity) => ({
    lat: activity.coordinates.latitude,
    lng: activity.coordinates.longitude,
  }));

  const polylineOptions = {
    strokeColor: "#6366f1",
    strokeOpacity: 0.8,
    strokeWeight: 3,
    icons: [
      {
        icon: {
          path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
          scale: 3,
          strokeColor: "#6366f1",
        },
        offset: "100%",
        repeat: "100px",
      },
    ],
  };

  return (
    <div className="relative">
      <GoogleMap
        mapContainerStyle={mapContainerStyle}
        center={center}
        zoom={zoom}
        options={mapOptions}
        onLoad={onMapLoad}
      >
        {/* Polyline connecting activities in order */}
        <Polyline path={path} options={polylineOptions} />

        {/* Markers for each activity */}
        {validActivities.map((activity, index) => (
          <Marker
            key={activity.id}
            position={{
              lat: activity.coordinates.latitude,
              lng: activity.coordinates.longitude,
            }}
            label={getMarkerLabel(index)}
            icon={{
              path: google.maps.SymbolPath.CIRCLE,
              fillColor: getCategoryColor(activity.category),
              fillOpacity: 1,
              strokeColor: "white",
              strokeWeight: 2,
              scale: 10,
            }}
            onClick={() => setSelectedActivity({ activity, index })}
          />
        ))}

        {/* Info Window for selected activity */}
        {selectedActivity && (
          <InfoWindow
            position={{
              lat: selectedActivity.activity.coordinates.latitude,
              lng: selectedActivity.activity.coordinates.longitude,
            }}
            onCloseClick={() => setSelectedActivity(null)}
          >
            <div className="p-2 max-w-xs">
              <h3 className="font-bold text-gray-900 mb-1 text-sm">
                {selectedActivity.index + 1}. {selectedActivity.activity.name}
              </h3>
              {selectedActivity.activity.description && (
                <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                  {selectedActivity.activity.description}
                </p>
              )}
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full font-medium">
                  {selectedActivity.activity.category}
                </span>
                <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full font-medium">
                  ⭐ {selectedActivity.activity.rating.toFixed(1)}
                </span>
                <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full font-medium">
                  ${selectedActivity.activity.cost.toFixed(0)}
                </span>
                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full font-medium">
                  {selectedActivity.activity.duration} min
                </span>
              </div>
            </div>
          </InfoWindow>
        )}
      </GoogleMap>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 text-xs">
        <p className="font-semibold text-gray-700 mb-2">Route Order</p>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-primary-500 border-2 border-white flex items-center justify-center">
            <span className="text-white text-[8px] font-bold">1</span>
          </div>
          <span className="text-gray-600">→</span>
          <div className="w-4 h-4 rounded-full bg-primary-500 border-2 border-white flex items-center justify-center">
            <span className="text-white text-[8px] font-bold">2</span>
          </div>
          <span className="text-gray-600">→</span>
          <div className="w-4 h-4 rounded-full bg-primary-500 border-2 border-white flex items-center justify-center">
            <span className="text-white text-[8px] font-bold">n</span>
          </div>
        </div>
        <p className="text-gray-500 mt-1 text-[10px]">Click markers for details</p>
      </div>
    </div>
  );
}
