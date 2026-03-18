"use client";

import { useEffect } from "react";

interface ToastProps {
  message: string;
  type: "error" | "success" | "info";
  onClose: () => void;
  duration?: number;
}

export default function Toast({
  message,
  type,
  onClose,
  duration = 5000,
}: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const styles =
    type === "error"
      ? "bg-gradient-to-r from-red-500 to-pink-500"
      : type === "success"
      ? "bg-gradient-to-r from-emerald-500 to-teal-500"
      : "bg-gradient-to-r from-blue-500 to-indigo-500";

  const icon =
    type === "error"
      ? "❌"
      : type === "success"
      ? "✓"
      : "ℹ";

  return (
    <div
      className={`fixed top-4 right-4 ${styles} text-white px-6 py-4 rounded-2xl shadow-2xl z-50 flex items-center gap-4 min-w-[320px] max-w-md animate-slide-in hover-lift border border-white/20`}
    >
      <div className="flex items-center justify-center w-8 h-8 bg-white/20 rounded-full flex-shrink-0">
        <span className="text-lg">{icon}</span>
      </div>
      <span className="flex-1 font-medium">{message}</span>
      <button
        onClick={onClose}
        className="text-white/80 hover:text-white transition-colors font-bold text-xl flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full hover:bg-white/20"
      >
        ×
      </button>
    </div>
  );
}

