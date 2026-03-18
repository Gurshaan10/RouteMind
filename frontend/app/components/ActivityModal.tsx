"use client";

interface ActivityModalProps {
  activity: {
    id: number;
    name: string;
    category: string;
    cost: number;
    duration: number;
    rating: number;
    coordinates: { latitude: number; longitude: number };
    tags?: string[] | null;
    description?: string | null;
  };
  onClose: () => void;
}

export default function ActivityModal({ activity, onClose }: ActivityModalProps) {
  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in"
      onClick={onClose}
    >
      <div
        className="glass-strong rounded-3xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-hidden animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-br from-primary-400/20 to-accent-400/20 rounded-t-3xl"></div>
          <div className="relative p-6 pb-4">
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-3xl font-bold text-gray-900 pr-8">{activity.name}</h3>
              <button
                onClick={onClose}
                className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 transition-colors w-10 h-10 flex items-center justify-center rounded-full hover:bg-white/50"
              >
                <span className="text-3xl leading-none">×</span>
              </button>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-4 py-1.5 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-full text-sm font-semibold shadow-lg">
                {activity.category}
              </span>
              <div className="flex items-center gap-1 bg-white/60 px-3 py-1.5 rounded-full">
                <span className="text-yellow-500">★</span>
                <span className="text-sm font-bold text-gray-900">{activity.rating.toFixed(1)}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 pt-4 space-y-5 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white/60 rounded-2xl p-4 text-center">
              <div className="text-2xl mb-1">💰</div>
              <div className="text-sm text-gray-600 font-medium">Cost</div>
              <div className="text-xl font-bold text-gray-900">${activity.cost.toFixed(2)}</div>
            </div>
            <div className="bg-white/60 rounded-2xl p-4 text-center">
              <div className="text-2xl mb-1">⏱️</div>
              <div className="text-sm text-gray-600 font-medium">Duration</div>
              <div className="text-xl font-bold text-gray-900">{activity.duration} min</div>
            </div>
          </div>

          {activity.description && (
            <div className="bg-white/60 rounded-2xl p-4">
              <h4 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
                <span>📝</span> Description
              </h4>
              <p className="text-gray-700 leading-relaxed">{activity.description}</p>
            </div>
          )}

          {activity.tags && activity.tags.length > 0 && (
            <div className="bg-white/60 rounded-2xl p-4">
              <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                <span>🏷️</span> Tags
              </h4>
              <div className="flex flex-wrap gap-2">
                {activity.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 rounded-full text-xs font-medium border border-gray-300/50"
                  >
                    {tag.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="bg-white/60 rounded-2xl p-4">
            <h4 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
              <span>📍</span> Location
            </h4>
            <p className="text-sm text-gray-600 font-mono bg-gray-100 px-3 py-2 rounded-lg">
              {activity.coordinates.latitude.toFixed(4)}, {activity.coordinates.longitude.toFixed(4)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

