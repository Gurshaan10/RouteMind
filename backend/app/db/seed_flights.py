"""Seed script to populate flight connections between cities."""
from app.db.session import SessionLocal
from app.db.models import City, Flight, Accommodation


def seed_flights():
    """Seed flight data between all cities in the database."""
    db = SessionLocal()

    try:
        # Check if flights already exist
        if db.query(Flight).count() > 0:
            print("Flights already seeded. Skipping...")
            return

        # Get all cities
        cities = db.query(City).all()
        city_map = {city.name: city.id for city in cities}

        print(f"Found {len(cities)} cities. Creating flight connections...")

        # Flight data: (origin, destination, airline, avg_price, duration_minutes, frequency)
        # Realistic flight times and prices based on actual routes
        flight_connections = [
            # San Francisco connections
            ("San Francisco", "New York", "United Airlines", 350, 330, "daily"),
            ("San Francisco", "Los Angeles", "Southwest", 120, 85, "daily"),
            ("San Francisco", "Paris", "Air France", 850, 660, "daily"),
            ("San Francisco", "Tokyo", "ANA", 950, 660, "daily"),
            ("San Francisco", "London", "British Airways", 800, 645, "daily"),

            # New York connections
            ("New York", "San Francisco", "United Airlines", 350, 360, "daily"),
            ("New York", "Los Angeles", "JetBlue", 250, 360, "daily"),
            ("New York", "Paris", "Delta", 600, 450, "daily"),
            ("New York", "Tokyo", "JAL", 1100, 810, "daily"),
            ("New York", "London", "British Airways", 550, 420, "daily"),
            ("New York", "Barcelona", "Iberia", 650, 480, "daily"),
            ("New York", "Rome", "Alitalia", 700, 510, "daily"),

            # Los Angeles connections
            ("Los Angeles", "San Francisco", "Southwest", 120, 75, "daily"),
            ("Los Angeles", "New York", "American Airlines", 280, 330, "daily"),
            ("Los Angeles", "Tokyo", "ANA", 900, 660, "daily"),
            ("Los Angeles", "Paris", "Air France", 900, 660, "daily"),

            # Paris connections
            ("Paris", "San Francisco", "Air France", 850, 690, "daily"),
            ("Paris", "New York", "Air France", 600, 480, "daily"),
            ("Paris", "Los Angeles", "Air France", 900, 690, "daily"),
            ("Paris", "London", "EasyJet", 120, 80, "daily"),
            ("Paris", "Barcelona", "Vueling", 150, 120, "daily"),
            ("Paris", "Rome", "Alitalia", 180, 125, "daily"),
            ("Paris", "Tokyo", "Air France", 1000, 780, "3x_week"),
            ("Paris", "Dubai", "Emirates", 450, 420, "daily"),

            # Tokyo connections
            ("Tokyo", "San Francisco", "ANA", 950, 630, "daily"),
            ("Tokyo", "New York", "JAL", 1100, 780, "daily"),
            ("Tokyo", "Los Angeles", "JAL", 900, 630, "daily"),
            ("Tokyo", "Paris", "JAL", 1000, 750, "3x_week"),
            ("Tokyo", "London", "British Airways", 1100, 720, "daily"),
            ("Tokyo", "Bangkok", "Thai Airways", 450, 360, "daily"),
            ("Tokyo", "Dubai", "Emirates", 800, 600, "3x_week"),

            # London connections
            ("London", "San Francisco", "British Airways", 800, 660, "daily"),
            ("London", "New York", "Virgin Atlantic", 550, 450, "daily"),
            ("London", "Paris", "Eurostar", 150, 135, "daily"),
            ("London", "Barcelona", "British Airways", 200, 140, "daily"),
            ("London", "Rome", "Ryanair", 150, 155, "daily"),
            ("London", "Dubai", "Emirates", 500, 420, "daily"),
            ("London", "Bangkok", "British Airways", 750, 660, "daily"),
            ("London", "Tokyo", "ANA", 1100, 720, "daily"),

            # Barcelona connections
            ("Barcelona", "Paris", "Vueling", 150, 120, "daily"),
            ("Barcelona", "New York", "Iberia", 650, 510, "daily"),
            ("Barcelona", "London", "Ryanair", 200, 140, "daily"),
            ("Barcelona", "Rome", "Vueling", 180, 115, "daily"),
            ("Barcelona", "Dubai", "Emirates", 550, 420, "3x_week"),

            # Rome connections
            ("Rome", "Paris", "Alitalia", 180, 125, "daily"),
            ("Rome", "New York", "Alitalia", 700, 540, "daily"),
            ("Rome", "London", "British Airways", 150, 155, "daily"),
            ("Rome", "Barcelona", "Alitalia", 180, 115, "daily"),
            ("Rome", "Dubai", "Emirates", 450, 360, "3x_week"),

            # Dubai connections
            ("Dubai", "Paris", "Emirates", 450, 450, "daily"),
            ("Dubai", "Tokyo", "Emirates", 800, 600, "3x_week"),
            ("Dubai", "London", "Emirates", 500, 420, "daily"),
            ("Dubai", "Barcelona", "Emirates", 550, 450, "3x_week"),
            ("Dubai", "Rome", "Emirates", 450, 390, "3x_week"),
            ("Dubai", "Bangkok", "Emirates", 350, 360, "daily"),

            # Bangkok connections
            ("Bangkok", "Tokyo", "Thai Airways", 450, 360, "daily"),
            ("Bangkok", "London", "Thai Airways", 750, 660, "daily"),
            ("Bangkok", "Dubai", "Emirates", 350, 360, "daily"),
        ]

        # Create flight records
        flights_created = 0
        for origin_name, dest_name, airline, price, duration, freq in flight_connections:
            if origin_name in city_map and dest_name in city_map:
                flight = Flight(
                    origin_city_id=city_map[origin_name],
                    destination_city_id=city_map[dest_name],
                    airline=airline,
                    avg_price=price,
                    avg_duration_minutes=duration,
                    frequency=freq
                )
                db.add(flight)
                flights_created += 1

        db.commit()
        print(f"✅ Successfully created {flights_created} flight connections!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding flights: {e}")
        raise
    finally:
        db.close()


def seed_accommodations():
    """Seed accommodation data for each city."""
    db = SessionLocal()

    try:
        # Check if accommodations already exist
        if db.query(Accommodation).count() > 0:
            print("Accommodations already seeded. Skipping...")
            return

        cities = db.query(City).all()

        # Accommodation templates by budget category
        # Each city gets 3 options: budget, midrange, luxury
        accommodation_data = [
            # San Francisco
            ("San Francisco", "HI San Francisco Downtown Hostel", "budget", 45, 4.2, 37.7749, -122.4194, "Clean hostel with shared kitchen and common areas", ["wifi", "breakfast", "lockers"]),
            ("San Francisco", "Hotel Zephyr", "midrange", 180, 4.3, 37.8080, -122.4177, "Modern hotel at Fisherman's Wharf with bay views", ["wifi", "breakfast", "pool", "parking"]),
            ("San Francisco", "Fairmont San Francisco", "luxury", 450, 4.7, 37.7926, -122.4103, "Historic luxury hotel atop Nob Hill", ["wifi", "breakfast", "pool", "spa", "concierge"]),

            # New York
            ("New York", "Bowery House", "budget", 60, 4.0, 40.7223, -73.9938, "Modern pod-style hostel in Lower East Side", ["wifi", "shared_bathroom", "lockers"]),
            ("New York", "Hilton Midtown", "midrange", 220, 4.2, 40.7589, -73.9851, "Central location near Times Square", ["wifi", "breakfast", "gym", "business_center"]),
            ("New York", "The Plaza Hotel", "luxury", 650, 4.8, 40.7644, -73.9745, "Iconic luxury hotel overlooking Central Park", ["wifi", "breakfast", "spa", "fine_dining", "concierge"]),

            # Los Angeles
            ("Los Angeles", "Samesun Venice Beach", "budget", 50, 4.1, 33.9850, -118.4695, "Beachside hostel with surfboard rentals", ["wifi", "breakfast", "kitchen", "beach_access"]),
            ("Los Angeles", "The Hollywood Roosevelt", "midrange", 200, 4.3, 34.1017, -118.3431, "Historic hotel on Hollywood Boulevard", ["wifi", "pool", "restaurant", "parking"]),
            ("Los Angeles", "Beverly Wilshire", "luxury", 550, 4.8, 34.0670, -118.3997, "Luxury hotel in the heart of Beverly Hills", ["wifi", "spa", "pool", "fine_dining", "valet"]),

            # Paris
            ("Paris", "St Christopher's Inn Canal", "budget", 40, 4.2, 48.8728, 2.3676, "Lively hostel near Canal Saint-Martin", ["wifi", "breakfast", "bar", "lockers"]),
            ("Paris", "Hotel Le Marais", "midrange", 160, 4.4, 48.8566, 2.3522, "Boutique hotel in historic Marais district", ["wifi", "breakfast", "concierge"]),
            ("Paris", "Le Meurice", "luxury", 800, 4.9, 48.8656, 2.3283, "Palace hotel overlooking Tuileries Garden", ["wifi", "breakfast", "spa", "michelin_dining", "concierge"]),

            # Tokyo
            ("Tokyo", "Khaosan Tokyo Kabuki", "budget", 35, 4.3, 35.7023, 139.7024, "Japanese-style capsule hotel near Asakusa", ["wifi", "shared_bathroom", "lounge"]),
            ("Tokyo", "Hotel Gracery Shinjuku", "midrange", 150, 4.4, 35.6938, 139.7006, "Modern hotel with Godzilla head on rooftop", ["wifi", "breakfast", "restaurant"]),
            ("Tokyo", "The Peninsula Tokyo", "luxury", 700, 4.8, 35.6751, 139.7634, "Luxury hotel near Imperial Palace", ["wifi", "breakfast", "spa", "pool", "michelin_dining"]),

            # London
            ("London", "Clink78", "budget", 45, 4.1, 51.5272, -0.1213, "Converted courthouse hostel near King's Cross", ["wifi", "breakfast", "bar", "lockers"]),
            ("London", "The Hoxton Holborn", "midrange", 180, 4.5, 51.5179, -0.1172, "Stylish hotel in Holborn district", ["wifi", "breakfast", "restaurant", "lobby_bar"]),
            ("London", "The Savoy", "luxury", 650, 4.8, 51.5106, -0.1204, "Iconic luxury hotel on the Thames", ["wifi", "breakfast", "spa", "pool", "butler_service"]),

            # Barcelona
            ("Barcelona", "TOC Hostel", "budget", 38, 4.3, 41.3851, 2.1734, "Design hostel near beach with rooftop terrace", ["wifi", "breakfast", "pool", "bar"]),
            ("Barcelona", "Hotel Jazz", "midrange", 140, 4.4, 41.3879, 2.1699, "Modern hotel on Passeig de Gràcia", ["wifi", "breakfast", "pool", "terrace"]),
            ("Barcelona", "Hotel Arts Barcelona", "luxury", 500, 4.7, 41.3858, 2.1965, "Beachfront luxury hotel with Michelin dining", ["wifi", "breakfast", "spa", "pool", "beach_access"]),

            # Rome
            ("Rome", "The Yellow", "budget", 42, 4.2, 41.9009, 12.4965, "Social hostel near Termini Station", ["wifi", "breakfast", "bar", "tours"]),
            ("Rome", "Hotel Artemide", "midrange", 170, 4.5, 41.9028, 12.4964, "4-star hotel near Via Veneto", ["wifi", "breakfast", "spa", "rooftop_bar"]),
            ("Rome", "Hotel Hassler Roma", "luxury", 750, 4.9, 41.9065, 12.4829, "Luxury hotel atop Spanish Steps", ["wifi", "breakfast", "michelin_dining", "spa", "concierge"]),

            # Dubai
            ("Dubai", "Rove Downtown", "budget", 70, 4.3, 25.1972, 55.2744, "Modern budget hotel near Burj Khalifa", ["wifi", "breakfast", "pool", "gym"]),
            ("Dubai", "Address Dubai Mall", "midrange", 250, 4.5, 25.1980, 55.2789, "Upscale hotel connected to Dubai Mall", ["wifi", "breakfast", "pool", "spa", "mall_access"]),
            ("Dubai", "Burj Al Arab", "luxury", 1500, 5.0, 25.1413, 55.1853, "World's only 7-star hotel", ["wifi", "breakfast", "butler", "spa", "private_beach", "helipad"]),

            # Bangkok
            ("Bangkok", "Lub d Bangkok Siam", "budget", 25, 4.4, 13.7463, 100.5332, "Trendy hostel near shopping district", ["wifi", "breakfast", "pool", "bar"]),
            ("Bangkok", "Novotel Bangkok Sukhumvit", "midrange", 90, 4.3, 13.7248, 100.5571, "Modern hotel on Sukhumvit Road", ["wifi", "breakfast", "pool", "spa"]),
            ("Bangkok", "Mandarin Oriental Bangkok", "luxury", 400, 4.8, 13.7248, 100.5167, "Legendary riverside luxury hotel", ["wifi", "breakfast", "spa", "michelin_dining", "river_cruise"]),
        ]

        # Create accommodation records
        accommodations_created = 0
        for city_name, name, category, price, rating, lat, lng, desc, amenities in accommodation_data:
            city = db.query(City).filter(City.name == city_name).first()
            if city:
                accommodation = Accommodation(
                    city_id=city.id,
                    name=name,
                    category=category,
                    avg_price_per_night=price,
                    rating=rating,
                    latitude=lat,
                    longitude=lng,
                    description=desc,
                    amenities=amenities
                )
                db.add(accommodation)
                accommodations_created += 1

        db.commit()
        print(f"✅ Successfully created {accommodations_created} accommodation options!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding accommodations: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌍 Seeding flight and accommodation data...")
    seed_flights()
    seed_accommodations()
    print("✅ All data seeded successfully!")
