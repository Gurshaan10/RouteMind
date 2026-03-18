import type { Metadata } from "next";
import "./globals.css";
import SessionProvider from "./components/SessionProvider";
import SessionMigrationWrapper from "./components/SessionMigrationWrapper";
import Header from "./components/Header";
import GoogleMapsProvider from "./components/GoogleMapsProvider";

export const metadata: Metadata = {
  title: "RouteMind - AI Travel Itinerary Planner",
  description: "Generate personalized, optimized travel itineraries powered by AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <SessionProvider>
          <GoogleMapsProvider>
            <SessionMigrationWrapper />
            <Header />
            {children}
          </GoogleMapsProvider>
        </SessionProvider>
      </body>
    </html>
  );
}

