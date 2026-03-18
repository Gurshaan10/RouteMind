"""Seed script to populate initial cities and activities."""
from datetime import time
from app.db.session import SessionLocal, engine, Base
from app.db.models import City, Activity


def init_db():
    """Initialize database with seed data."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(City).count() > 0:
            print("Database already seeded. Skipping...")
            return
        
        # Create San Francisco
        sf = City(
            name="San Francisco",
            country="United States",
            time_zone="America/Los_Angeles",
            default_currency="USD"
        )
        db.add(sf)
        db.flush()
        
        # San Francisco activities
        sf_activities = [
            Activity(
                city_id=sf.id,
                name="Golden Gate Bridge",
                category="nature",
                base_cost=0.0,
                avg_duration_minutes=60,
                rating=4.8,
                latitude=37.8199,
                longitude=-122.4783,
                open_time=None,
                close_time=None,
                description="Iconic suspension bridge spanning the Golden Gate strait."
            ),
            Activity(
                city_id=sf.id,
                name="Alcatraz Island",
                category="culture",
                base_cost=45.0,
                avg_duration_minutes=180,
                rating=4.7,
                latitude=37.8267,
                longitude=-122.4230,
                open_time=time(9, 0),
                close_time=time(18, 30),
                description="Former federal prison on an island in San Francisco Bay."
            ),
            Activity(
                city_id=sf.id,
                name="Fisherman's Wharf",
                category="food",
                base_cost=30.0,
                avg_duration_minutes=120,
                rating=4.2,
                latitude=37.8080,
                longitude=-122.4177,
                open_time=time(9, 0),
                close_time=time(21, 0),
                description="Historic waterfront district with seafood restaurants and shops."
            ),
            Activity(
                city_id=sf.id,
                name="Chinatown",
                category="culture",
                base_cost=20.0,
                avg_duration_minutes=90,
                rating=4.5,
                latitude=37.7941,
                longitude=-122.4078,
                open_time=time(10, 0),
                close_time=time(20, 0),
                description="Largest Chinatown outside of Asia with authentic cuisine and shops."
            ),
            Activity(
                city_id=sf.id,
                name="Lombard Street",
                category="nature",
                base_cost=0.0,
                avg_duration_minutes=30,
                rating=4.3,
                latitude=37.8021,
                longitude=-122.4187,
                open_time=None,
                close_time=None,
                description="Famous crooked street with eight hairpin turns."
            ),
            Activity(
                city_id=sf.id,
                name="Golden Gate Park",
                category="nature",
                base_cost=0.0,
                avg_duration_minutes=120,
                rating=4.6,
                latitude=37.7694,
                longitude=-122.4862,
                open_time=time(5, 0),
                close_time=time(22, 0),
                description="Large urban park with gardens, museums, and recreational areas."
            ),
            Activity(
                city_id=sf.id,
                name="Museum of Modern Art (SFMOMA)",
                category="culture",
                base_cost=25.0,
                avg_duration_minutes=150,
                rating=4.4,
                latitude=37.7857,
                longitude=-122.4011,
                open_time=time(10, 0),
                close_time=time(17, 0),
                description="Premier modern and contemporary art museum."
            ),
            Activity(
                city_id=sf.id,
                name="Twin Peaks",
                category="nature",
                base_cost=0.0,
                avg_duration_minutes=45,
                rating=4.7,
                latitude=37.7544,
                longitude=-122.4477,
                open_time=None,
                close_time=None,
                description="Scenic viewpoint offering panoramic views of the city."
            ),
            Activity(
                city_id=sf.id,
                name="Cable Car Ride",
                category="adventure",
                base_cost=8.0,
                avg_duration_minutes=30,
                rating=4.3,
                latitude=37.7946,
                longitude=-122.4094,
                open_time=time(7, 0),
                close_time=time(22, 0),
                description="Historic cable car system, a moving national landmark."
            ),
            Activity(
                city_id=sf.id,
                name="Mission District Murals",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=90,
                rating=4.5,
                latitude=37.7599,
                longitude=-122.4148,
                open_time=None,
                close_time=None,
                description="Colorful street art and murals in the Mission District."
            ),
            Activity(
                city_id=sf.id,
                name="Coit Tower",
                category="culture",
                base_cost=10.0,
                avg_duration_minutes=60,
                rating=4.2,
                latitude=37.8024,
                longitude=-122.4058,
                open_time=time(10, 0),
                close_time=time(17, 0),
                description="Art Deco tower with murals and city views."
            ),
            Activity(
                city_id=sf.id,
                name="Japanese Tea Garden",
                category="nature",
                base_cost=12.0,
                avg_duration_minutes=60,
                rating=4.4,
                latitude=37.7702,
                longitude=-122.4701,
                open_time=time(9, 0),
                close_time=time(17, 45),
                description="Oldest public Japanese garden in the United States."
            ),
            Activity(
                city_id=sf.id,
                name="Ferry Building Marketplace",
                category="food",
                base_cost=25.0,
                avg_duration_minutes=90,
                rating=4.6,
                latitude=37.7956,
                longitude=-122.3933,
                open_time=time(7, 0),
                close_time=time(20, 0),
                description="Historic building with artisanal food vendors and farmers market."
            ),
            Activity(
                city_id=sf.id,
                name="Palace of Fine Arts",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=45,
                rating=4.5,
                latitude=37.8029,
                longitude=-122.4488,
                open_time=None,
                close_time=None,
                description="Neoclassical structure with a beautiful rotunda and lagoon."
            ),
            Activity(
                city_id=sf.id,
                name="Haight-Ashbury",
                category="culture",
                base_cost=15.0,
                avg_duration_minutes=90,
                rating=4.3,
                latitude=37.7699,
                longitude=-122.4469,
                open_time=time(10, 0),
                close_time=time(20, 0),
                description="Historic neighborhood known for its role in the 1960s counterculture."
            ),
            Activity(
                city_id=sf.id,
                name="Sutro Baths Ruins",
                category="nature",
                base_cost=0.0,
                avg_duration_minutes=60,
                rating=4.4,
                latitude=37.7780,
                longitude=-122.5144,
                open_time=None,
                close_time=None,
                description="Remains of a historic public bathhouse with ocean views."
            ),
            Activity(
                city_id=sf.id,
                name="Union Square",
                category="shopping",
                base_cost=50.0,
                avg_duration_minutes=120,
                rating=4.2,
                latitude=37.7879,
                longitude=-122.4075,
                open_time=time(9, 0),
                close_time=time(21, 0),
                description="Shopping and dining hub in downtown San Francisco."
            ),
            Activity(
                city_id=sf.id,
                name="California Academy of Sciences",
                category="culture",
                base_cost=40.0,
                avg_duration_minutes=180,
                rating=4.6,
                latitude=37.7699,
                longitude=-122.4661,
                open_time=time(9, 30),
                close_time=time(17, 0),
                description="Natural history museum with aquarium, planetarium, and rainforest."
            ),
            Activity(
                city_id=sf.id,
                name="Baker Beach",
                category="beaches",
                base_cost=0.0,
                avg_duration_minutes=120,
                rating=4.5,
                latitude=37.7936,
                longitude=-122.4838,
                open_time=None,
                close_time=None,
                description="Scenic beach with views of the Golden Gate Bridge."
            ),
            Activity(
                city_id=sf.id,
                name="North Beach",
                category="food",
                base_cost=35.0,
                avg_duration_minutes=120,
                rating=4.4,
                latitude=37.8050,
                longitude=-122.4096,
                open_time=time(11, 0),
                close_time=time(23, 0),
                description="Little Italy neighborhood with Italian restaurants and cafes."
            ),
        ]
        
        for activity in sf_activities:
            db.add(activity)
        
        # Create Paris
        paris = City(
            name="Paris",
            country="France",
            time_zone="Europe/Paris",
            default_currency="EUR"
        )
        db.add(paris)
        db.flush()
        
        # Paris activities
        paris_activities = [
            Activity(
                city_id=paris.id,
                name="Eiffel Tower",
                category="culture",
                base_cost=29.0,
                avg_duration_minutes=120,
                rating=4.6,
                latitude=48.8584,
                longitude=2.2945,
                open_time=time(9, 30),
                close_time=time(23, 45),
                description="Iconic iron lattice tower, symbol of Paris."
            ),
            Activity(
                city_id=paris.id,
                name="Louvre Museum",
                category="culture",
                base_cost=17.0,
                avg_duration_minutes=240,
                rating=4.7,
                latitude=48.8606,
                longitude=2.3376,
                open_time=time(9, 0),
                close_time=time(18, 0),
                description="World's largest art museum and historic monument."
            ),
            Activity(
                city_id=paris.id,
                name="Notre-Dame Cathedral",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=60,
                rating=4.7,
                latitude=48.8530,
                longitude=2.3499,
                open_time=time(8, 0),
                close_time=time(18, 45),
                description="Medieval Catholic cathedral (currently under restoration)."
            ),
            Activity(
                city_id=paris.id,
                name="Arc de Triomphe",
                category="culture",
                base_cost=13.0,
                avg_duration_minutes=60,
                rating=4.6,
                latitude=48.8738,
                longitude=2.2950,
                open_time=time(10, 0),
                close_time=time(22, 30),
                description="Monumental arch honoring those who fought for France."
            ),
            Activity(
                city_id=paris.id,
                name="Champs-Élysées",
                category="shopping",
                base_cost=50.0,
                avg_duration_minutes=90,
                rating=4.4,
                latitude=48.8698,
                longitude=2.3081,
                open_time=time(9, 0),
                close_time=time(22, 0),
                description="Famous avenue with shops, cafes, and theaters."
            ),
            Activity(
                city_id=paris.id,
                name="Montmartre & Sacré-Cœur",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=120,
                rating=4.7,
                latitude=48.8867,
                longitude=2.3431,
                open_time=time(6, 0),
                close_time=time(22, 30),
                description="Historic hilltop neighborhood with basilica and artistic heritage."
            ),
            Activity(
                city_id=paris.id,
                name="Seine River Cruise",
                category="adventure",
                base_cost=15.0,
                avg_duration_minutes=60,
                rating=4.5,
                latitude=48.8566,
                longitude=2.3522,
                open_time=time(10, 0),
                close_time=time(22, 0),
                description="Boat tour along the Seine River with views of major landmarks."
            ),
            Activity(
                city_id=paris.id,
                name="Musée d'Orsay",
                category="culture",
                base_cost=16.0,
                avg_duration_minutes=180,
                rating=4.7,
                latitude=48.8600,
                longitude=2.3266,
                open_time=time(9, 30),
                close_time=time(18, 0),
                description="Impressionist and post-impressionist art museum."
            ),
            Activity(
                city_id=paris.id,
                name="Versailles Palace",
                category="culture",
                base_cost=27.0,
                avg_duration_minutes=300,
                rating=4.6,
                latitude=48.8049,
                longitude=2.1204,
                open_time=time(9, 0),
                close_time=time(18, 30),
                description="Opulent royal château and gardens (day trip from Paris)."
            ),
            Activity(
                city_id=paris.id,
                name="Latin Quarter",
                category="food",
                base_cost=30.0,
                avg_duration_minutes=120,
                rating=4.5,
                latitude=48.8503,
                longitude=2.3431,
                open_time=time(11, 0),
                close_time=time(23, 0),
                description="Historic neighborhood with bistros and cafes."
            ),
            Activity(
                city_id=paris.id,
                name="Sainte-Chapelle",
                category="culture",
                base_cost=11.5,
                avg_duration_minutes=45,
                rating=4.6,
                latitude=48.8554,
                longitude=2.3450,
                open_time=time(9, 0),
                close_time=time(17, 0),
                description="Gothic chapel famous for its stunning stained glass windows."
            ),
            Activity(
                city_id=paris.id,
                name="Marais District",
                category="culture",
                base_cost=25.0,
                avg_duration_minutes=120,
                rating=4.5,
                latitude=48.8566,
                longitude=2.3622,
                open_time=time(10, 0),
                close_time=time(20, 0),
                description="Historic district with trendy shops, galleries, and cafes."
            ),
            Activity(
                city_id=paris.id,
                name="Père Lachaise Cemetery",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=90,
                rating=4.4,
                latitude=48.8614,
                longitude=2.3933,
                open_time=time(8, 0),
                close_time=time(18, 0),
                description="Famous cemetery with graves of notable figures."
            ),
            Activity(
                city_id=paris.id,
                name="Musée Rodin",
                category="culture",
                base_cost=13.0,
                avg_duration_minutes=90,
                rating=4.6,
                latitude=48.8552,
                longitude=2.3158,
                open_time=time(10, 0),
                close_time=time(18, 30),
                description="Museum dedicated to sculptor Auguste Rodin with beautiful gardens."
            ),
            Activity(
                city_id=paris.id,
                name="Place de la Bastille",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=30,
                rating=4.2,
                latitude=48.8532,
                longitude=2.3694,
                open_time=None,
                close_time=None,
                description="Historic square marking the site of the former Bastille prison."
            ),
            Activity(
                city_id=paris.id,
                name="Jardin du Luxembourg",
                category="nature",
                base_cost=0.0,
                avg_duration_minutes=90,
                rating=4.6,
                latitude=48.8462,
                longitude=2.3372,
                open_time=time(7, 30),
                close_time=time(21, 30),
                description="Beautiful public park with formal gardens and fountains."
            ),
            Activity(
                city_id=paris.id,
                name="Catacombs of Paris",
                category="adventure",
                base_cost=29.0,
                avg_duration_minutes=90,
                rating=4.4,
                latitude=48.8339,
                longitude=2.3324,
                open_time=time(10, 0),
                close_time=time(20, 30),
                description="Underground ossuaries holding remains of millions of Parisians."
            ),
            Activity(
                city_id=paris.id,
                name="Shakespeare and Company",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=45,
                rating=4.5,
                latitude=48.8534,
                longitude=2.3458,
                open_time=time(10, 0),
                close_time=time(22, 0),
                description="Famous English-language bookstore with literary history."
            ),
            Activity(
                city_id=paris.id,
                name="Place des Vosges",
                category="nature",
                base_cost=0.0,
                avg_duration_minutes=60,
                rating=4.5,
                latitude=48.8561,
                longitude=2.3656,
                open_time=None,
                close_time=None,
                description="Oldest planned square in Paris with elegant architecture."
            ),
            Activity(
                city_id=paris.id,
                name="Musée Picasso",
                category="culture",
                base_cost=14.0,
                avg_duration_minutes=120,
                rating=4.5,
                latitude=48.8596,
                longitude=2.3622,
                open_time=time(10, 30),
                close_time=time(18, 0),
                description="Museum dedicated to Pablo Picasso's works."
            ),
            Activity(
                city_id=paris.id,
                name="Bateaux Mouches",
                category="adventure",
                base_cost=15.0,
                avg_duration_minutes=70,
                rating=4.3,
                latitude=48.8611,
                longitude=2.3253,
                open_time=time(10, 0),
                close_time=time(22, 30),
                description="Popular boat tours on the Seine River."
            ),
            Activity(
                city_id=paris.id,
                name="Le Marais Food Tour",
                category="food",
                base_cost=85.0,
                avg_duration_minutes=180,
                rating=4.7,
                latitude=48.8566,
                longitude=2.3622,
                open_time=time(11, 0),
                close_time=time(19, 0),
                description="Guided culinary tour through the Marais district."
            ),
        ]
        
        for activity in paris_activities:
            db.add(activity)
        
        # Add tags to existing activities (update in place)
        # This is a simple approach - in production you might want a migration
        all_activities = db.query(Activity).all()
        for activity in all_activities:
            if activity.tags is None:
                # Assign tags based on category and characteristics
                tags = []
                if activity.category in ["culture", "nature"]:
                    tags.append("family_friendly")
                if activity.base_cost == 0.0:
                    tags.append("budget_friendly")
                if activity.category == "nature":
                    tags.append("outdoor")
                if activity.category in ["culture", "shopping"]:
                    tags.append("indoor")
                if activity.rating >= 4.5:
                    tags.append("highly_rated")
                activity.tags = tags if tags else None
        
        # Create New York
        nyc = City(
            name="New York",
            country="United States",
            time_zone="America/New_York",
            default_currency="USD"
        )
        db.add(nyc)
        db.flush()
        
        nyc_activities = [
            Activity(
                city_id=nyc.id,
                name="Statue of Liberty",
                category="culture",
                base_cost=24.0,
                avg_duration_minutes=180,
                rating=4.6,
                latitude=40.6892,
                longitude=-74.0445,
                open_time=time(9, 0),
                close_time=time(17, 0),
                description="Iconic symbol of freedom and democracy.",
                tags=["family_friendly", "highly_rated", "outdoor"]
            ),
            Activity(
                city_id=nyc.id,
                name="Central Park",
                category="nature",
                base_cost=0.0,
                avg_duration_minutes=120,
                rating=4.7,
                latitude=40.7829,
                longitude=-73.9654,
                open_time=time(6, 0),
                close_time=time(23, 0),
                description="843-acre urban park in Manhattan.",
                tags=["family_friendly", "budget_friendly", "outdoor", "highly_rated"]
            ),
            Activity(
                city_id=nyc.id,
                name="Times Square",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=60,
                rating=4.3,
                latitude=40.7580,
                longitude=-73.9855,
                open_time=None,
                close_time=None,
                description="Famous commercial intersection and entertainment hub.",
                tags=["family_friendly", "budget_friendly", "indoor"]
            ),
            Activity(
                city_id=nyc.id,
                name="Metropolitan Museum of Art",
                category="culture",
                base_cost=30.0,
                avg_duration_minutes=240,
                rating=4.7,
                latitude=40.7794,
                longitude=-73.9632,
                open_time=time(10, 0),
                close_time=time(17, 30),
                description="One of the world's largest and finest art museums.",
                tags=["family_friendly", "indoor", "highly_rated"]
            ),
            Activity(
                city_id=nyc.id,
                name="Brooklyn Bridge",
                category="nature",
                base_cost=0.0,
                avg_duration_minutes=90,
                rating=4.8,
                latitude=40.7061,
                longitude=-73.9969,
                open_time=None,
                close_time=None,
                description="Historic suspension bridge connecting Manhattan and Brooklyn.",
                tags=["family_friendly", "budget_friendly", "outdoor", "highly_rated"]
            ),
            Activity(
                city_id=nyc.id,
                name="Empire State Building",
                category="culture",
                base_cost=44.0,
                avg_duration_minutes=120,
                rating=4.5,
                latitude=40.7484,
                longitude=-73.9857,
                open_time=time(8, 0),
                close_time=time(23, 0),
                description="Art Deco skyscraper with observation decks.",
                tags=["family_friendly", "indoor", "highly_rated"]
            ),
            Activity(
                city_id=nyc.id,
                name="High Line",
                category="nature",
                base_cost=0.0,
                avg_duration_minutes=90,
                rating=4.6,
                latitude=40.7480,
                longitude=-74.0048,
                open_time=time(7, 0),
                close_time=time(22, 0),
                description="Elevated linear park built on a former railway.",
                tags=["family_friendly", "budget_friendly", "outdoor", "highly_rated"]
            ),
            Activity(
                city_id=nyc.id,
                name="Broadway Show",
                category="culture",
                base_cost=120.0,
                avg_duration_minutes=150,
                rating=4.8,
                latitude=40.7590,
                longitude=-73.9845,
                open_time=time(19, 0),
                close_time=time(22, 0),
                description="World-famous theater district performances.",
                tags=["indoor", "highly_rated"]
            ),
        ]
        
        for activity in nyc_activities:
            db.add(activity)
        
        # Create London
        london = City(
            name="London",
            country="United Kingdom",
            time_zone="Europe/London",
            default_currency="GBP"
        )
        db.add(london)
        db.flush()
        
        london_activities = [
            Activity(
                city_id=london.id,
                name="Big Ben",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=30,
                rating=4.6,
                latitude=51.4994,
                longitude=-0.1245,
                open_time=None,
                close_time=None,
                description="Iconic clock tower and symbol of London.",
                tags=["family_friendly", "budget_friendly", "outdoor", "highly_rated"]
            ),
            Activity(
                city_id=london.id,
                name="British Museum",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=180,
                rating=4.7,
                latitude=51.5194,
                longitude=-0.1270,
                open_time=time(10, 0),
                close_time=time(17, 0),
                description="World's first national public museum.",
                tags=["family_friendly", "budget_friendly", "indoor", "highly_rated"]
            ),
            Activity(
                city_id=london.id,
                name="Tower of London",
                category="culture",
                base_cost=33.0,
                avg_duration_minutes=180,
                rating=4.6,
                latitude=51.5081,
                longitude=-0.0759,
                open_time=time(9, 0),
                close_time=time(17, 30),
                description="Historic castle and home of the Crown Jewels.",
                tags=["family_friendly", "indoor", "highly_rated"]
            ),
            Activity(
                city_id=london.id,
                name="Hyde Park",
                category="nature",
                base_cost=0.0,
                avg_duration_minutes=120,
                rating=4.6,
                latitude=51.5073,
                longitude=-0.1657,
                open_time=time(5, 0),
                close_time=time(23, 0),
                description="Large royal park in central London.",
                tags=["family_friendly", "budget_friendly", "outdoor", "highly_rated"]
            ),
            Activity(
                city_id=london.id,
                name="Westminster Abbey",
                category="culture",
                base_cost=27.0,
                avg_duration_minutes=90,
                rating=4.7,
                latitude=51.4994,
                longitude=-0.1273,
                open_time=time(9, 30),
                close_time=time(15, 30),
                description="Gothic church and coronation site.",
                tags=["family_friendly", "indoor", "highly_rated"]
            ),
            Activity(
                city_id=london.id,
                name="London Eye",
                category="adventure",
                base_cost=32.0,
                avg_duration_minutes=30,
                rating=4.4,
                latitude=51.5033,
                longitude=-0.1195,
                open_time=time(10, 0),
                close_time=time(20, 30),
                description="Giant observation wheel on the South Bank.",
                tags=["family_friendly", "indoor", "highly_rated"]
            ),
            Activity(
                city_id=london.id,
                name="Camden Market",
                category="shopping",
                base_cost=20.0,
                avg_duration_minutes=120,
                rating=4.3,
                latitude=51.5416,
                longitude=-0.1466,
                open_time=time(10, 0),
                close_time=time(18, 0),
                description="Vibrant market with food, fashion, and crafts.",
                tags=["family_friendly", "budget_friendly", "indoor"]
            ),
        ]
        
        for activity in london_activities:
            db.add(activity)
        
        # Create Tokyo
        tokyo = City(
            name="Tokyo",
            country="Japan",
            time_zone="Asia/Tokyo",
            default_currency="JPY"
        )
        db.add(tokyo)
        db.flush()
        
        tokyo_activities = [
            Activity(
                city_id=tokyo.id,
                name="Senso-ji Temple",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=90,
                rating=4.6,
                latitude=35.7148,
                longitude=139.7967,
                open_time=time(6, 0),
                close_time=time(17, 0),
                description="Tokyo's oldest temple in Asakusa.",
                tags=["family_friendly", "budget_friendly", "outdoor", "highly_rated"]
            ),
            Activity(
                city_id=tokyo.id,
                name="Shibuya Crossing",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=30,
                rating=4.5,
                latitude=35.6598,
                longitude=139.7006,
                open_time=None,
                close_time=None,
                description="World's busiest pedestrian crossing.",
                tags=["family_friendly", "budget_friendly", "outdoor"]
            ),
            Activity(
                city_id=tokyo.id,
                name="Tokyo Skytree",
                category="culture",
                base_cost=18.0,
                avg_duration_minutes=120,
                rating=4.6,
                latitude=35.7101,
                longitude=139.8107,
                open_time=time(8, 0),
                close_time=time(22, 0),
                description="Tallest structure in Japan with observation decks.",
                tags=["family_friendly", "indoor", "highly_rated"]
            ),
            Activity(
                city_id=tokyo.id,
                name="Tsukiji Outer Market",
                category="food",
                base_cost=30.0,
                avg_duration_minutes=120,
                rating=4.7,
                latitude=35.6654,
                longitude=139.7706,
                open_time=time(5, 0),
                close_time=time(14, 0),
                description="Famous fish market with fresh sushi and street food.",
                tags=["budget_friendly", "outdoor", "highly_rated"]
            ),
            Activity(
                city_id=tokyo.id,
                name="Meiji Shrine",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=90,
                rating=4.7,
                latitude=35.6764,
                longitude=139.6993,
                open_time=time(6, 30),
                close_time=time(16, 0),
                description="Shinto shrine dedicated to Emperor Meiji.",
                tags=["family_friendly", "budget_friendly", "outdoor", "highly_rated"]
            ),
            Activity(
                city_id=tokyo.id,
                name="Harajuku",
                category="shopping",
                base_cost=25.0,
                avg_duration_minutes=120,
                rating=4.4,
                latitude=35.6702,
                longitude=139.7026,
                open_time=time(10, 0),
                close_time=time(20, 0),
                description="Fashion district known for youth culture.",
                tags=["family_friendly", "budget_friendly", "indoor"]
            ),
        ]
        
        for activity in tokyo_activities:
            db.add(activity)
        
        # Create Rome
        rome = City(
            name="Rome",
            country="Italy",
            time_zone="Europe/Rome",
            default_currency="EUR"
        )
        db.add(rome)
        db.flush()
        
        rome_activities = [
            Activity(
                city_id=rome.id,
                name="Colosseum",
                category="culture",
                base_cost=18.0,
                avg_duration_minutes=120,
                rating=4.7,
                latitude=41.8902,
                longitude=12.4922,
                open_time=time(9, 0),
                close_time=time(19, 0),
                description="Ancient Roman amphitheater, symbol of Rome.",
                tags=["family_friendly", "outdoor", "highly_rated"]
            ),
            Activity(
                city_id=rome.id,
                name="Vatican Museums",
                category="culture",
                base_cost=17.0,
                avg_duration_minutes=240,
                rating=4.7,
                latitude=41.9029,
                longitude=12.4534,
                open_time=time(9, 0),
                close_time=time(18, 0),
                description="Museums containing the Sistine Chapel.",
                tags=["family_friendly", "indoor", "highly_rated"]
            ),
            Activity(
                city_id=rome.id,
                name="Trevi Fountain",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=30,
                rating=4.6,
                latitude=41.9009,
                longitude=12.4833,
                open_time=None,
                close_time=None,
                description="Baroque fountain and tourist attraction.",
                tags=["family_friendly", "budget_friendly", "outdoor", "highly_rated"]
            ),
            Activity(
                city_id=rome.id,
                name="Pantheon",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=60,
                rating=4.7,
                latitude=41.8986,
                longitude=12.4769,
                open_time=time(9, 0),
                close_time=time(19, 0),
                description="Ancient Roman temple, now a church.",
                tags=["family_friendly", "budget_friendly", "indoor", "highly_rated"]
            ),
            Activity(
                city_id=rome.id,
                name="Roman Forum",
                category="culture",
                base_cost=18.0,
                avg_duration_minutes=120,
                rating=4.6,
                latitude=41.8925,
                longitude=12.4853,
                open_time=time(8, 30),
                close_time=time(19, 0),
                description="Ancient Roman government center.",
                tags=["family_friendly", "outdoor", "highly_rated"]
            ),
        ]
        
        for activity in rome_activities:
            db.add(activity)
        
        # Create Barcelona
        barcelona = City(
            name="Barcelona",
            country="Spain",
            time_zone="Europe/Madrid",
            default_currency="EUR"
        )
        db.add(barcelona)
        db.flush()
        
        barcelona_activities = [
            Activity(
                city_id=barcelona.id,
                name="Sagrada Familia",
                category="culture",
                base_cost=26.0,
                avg_duration_minutes=120,
                rating=4.7,
                latitude=41.4036,
                longitude=2.1744,
                open_time=time(9, 0),
                close_time=time(18, 0),
                description="Gaudí's unfinished masterpiece basilica.",
                tags=["family_friendly", "indoor", "highly_rated"]
            ),
            Activity(
                city_id=barcelona.id,
                name="Park Güell",
                category="nature",
                base_cost=10.0,
                avg_duration_minutes=120,
                rating=4.6,
                latitude=41.4145,
                longitude=2.1527,
                open_time=time(8, 0),
                close_time=time(21, 30),
                description="Colorful park designed by Gaudí.",
                tags=["family_friendly", "budget_friendly", "outdoor", "highly_rated"]
            ),
            Activity(
                city_id=barcelona.id,
                name="La Rambla",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=90,
                rating=4.3,
                latitude=41.3809,
                longitude=2.1718,
                open_time=None,
                close_time=None,
                description="Famous tree-lined pedestrian street.",
                tags=["family_friendly", "budget_friendly", "outdoor"]
            ),
            Activity(
                city_id=barcelona.id,
                name="Gothic Quarter",
                category="culture",
                base_cost=0.0,
                avg_duration_minutes=120,
                rating=4.5,
                latitude=41.3833,
                longitude=2.1769,
                open_time=None,
                close_time=None,
                description="Medieval neighborhood with narrow streets.",
                tags=["family_friendly", "budget_friendly", "outdoor", "highly_rated"]
            ),
            Activity(
                city_id=barcelona.id,
                name="Camp Nou",
                category="culture",
                base_cost=28.0,
                avg_duration_minutes=120,
                rating=4.6,
                latitude=41.3809,
                longitude=2.1228,
                open_time=time(9, 30),
                close_time=time(19, 30),
                description="FC Barcelona's iconic stadium.",
                tags=["family_friendly", "indoor", "highly_rated"]
            ),
        ]
        
        for activity in barcelona_activities:
            db.add(activity)
        
        # Create Sydney
        sydney = City(
            name="Sydney",
            country="Australia",
            time_zone="Australia/Sydney",
            default_currency="AUD"
        )
        db.add(sydney)
        db.flush()
        
        sydney_activities = [
            Activity(
                city_id=sydney.id,
                name="Sydney Opera House",
                category="culture",
                base_cost=43.0,
                avg_duration_minutes=120,
                rating=4.7,
                latitude=-33.8568,
                longitude=151.2153,
                open_time=time(9, 0),
                close_time=time(17, 0),
                description="Iconic performing arts center.",
                tags=["family_friendly", "indoor", "highly_rated"]
            ),
            Activity(
                city_id=sydney.id,
                name="Sydney Harbour Bridge",
                category="nature",
                base_cost=0.0,
                avg_duration_minutes=60,
                rating=4.6,
                latitude=-33.8523,
                longitude=151.2108,
                open_time=None,
                close_time=None,
                description="Steel arch bridge across Sydney Harbour.",
                tags=["family_friendly", "budget_friendly", "outdoor", "highly_rated"]
            ),
            Activity(
                city_id=sydney.id,
                name="Bondi Beach",
                category="beaches",
                base_cost=0.0,
                avg_duration_minutes=180,
                rating=4.6,
                latitude=-33.8915,
                longitude=151.2767,
                open_time=None,
                close_time=None,
                description="Famous beach and surf spot.",
                tags=["family_friendly", "budget_friendly", "outdoor", "highly_rated"]
            ),
            Activity(
                city_id=sydney.id,
                name="Royal Botanic Gardens",
                category="nature",
                base_cost=0.0,
                avg_duration_minutes=120,
                rating=4.6,
                latitude=-33.8641,
                longitude=151.2169,
                open_time=time(7, 0),
                close_time=time(20, 0),
                description="Beautiful gardens with harbor views.",
                tags=["family_friendly", "budget_friendly", "outdoor", "highly_rated"]
            ),
        ]
        
        for activity in sydney_activities:
            db.add(activity)
        
        # Create Dubai
        dubai = City(
            name="Dubai",
            country="United Arab Emirates",
            time_zone="Asia/Dubai",
            default_currency="AED"
        )
        db.add(dubai)
        db.flush()
        
        dubai_activities = [
            Activity(
                city_id=dubai.id,
                name="Burj Khalifa",
                category="culture",
                base_cost=149.0,
                avg_duration_minutes=120,
                rating=4.6,
                latitude=25.1972,
                longitude=55.2744,
                open_time=time(8, 30),
                close_time=time(23, 0),
                description="World's tallest building with observation decks.",
                tags=["family_friendly", "indoor", "highly_rated"]
            ),
            Activity(
                city_id=dubai.id,
                name="Dubai Mall",
                category="shopping",
                base_cost=0.0,
                avg_duration_minutes=180,
                rating=4.5,
                latitude=25.1984,
                longitude=55.2794,
                open_time=time(10, 0),
                close_time=time(23, 0),
                description="One of the world's largest shopping malls.",
                tags=["family_friendly", "budget_friendly", "indoor"]
            ),
            Activity(
                city_id=dubai.id,
                name="Palm Jumeirah",
                category="nature",
                base_cost=0.0,
                avg_duration_minutes=90,
                rating=4.4,
                latitude=25.1124,
                longitude=55.1390,
                open_time=None,
                close_time=None,
                description="Artificial palm-shaped island.",
                tags=["family_friendly", "budget_friendly", "outdoor"]
            ),
        ]
        
        for activity in dubai_activities:
            db.add(activity)
        
        db.commit()
        print(f"Seeded database with {db.query(City).count()} cities and {db.query(Activity).count()} activities.")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()

