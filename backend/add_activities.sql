-- Add viral and trending activities to major cities (2024-2025)
-- NEW YORK CITY - Adding 14 more activities to reach 22 total

INSERT INTO activities (city_id, name, category, cost, duration, rating, coordinates, tags, description) VALUES
-- New York (city_id = 44)
(44, 'Summit One Vanderbilt', 'culture', 45, 90, 4.8, '(40.752726, -73.978433)', ARRAY['observation-deck', 'instagram-worthy', 'modern', 'trending'], 'Viral immersive art installation and observation deck with stunning skyline views and mirror rooms'),
(44, 'ARTECHOUSE NYC', 'culture', 35, 75, 4.7, '(40.739235, -74.006668)', ARRAY['digital-art', 'immersive', 'instagram-worthy', 'family-friendly'], 'Cutting-edge immersive digital art experiences that are highly Instagrammable'),
(44, 'Brooklyn Bridge Park', 'nature', 0, 120, 4.8, '(40.702613, -73.996365)', ARRAY['waterfront', 'free', 'scenic-views', 'outdoor'], 'Beautiful waterfront park with stunning Manhattan skyline views and piers'),
(44, 'Little Island', 'nature', 0, 60, 4.6, '(40.746044, -74.006666)', ARRAY['park', 'architecture', 'free', 'trending'], 'Unique elevated park on the Hudson River, opened 2021, very Instagram-worthy'),
(44, 'DUMBO Brooklyn', 'culture', 0, 90, 4.7, '(40.703381, -73.988781)', ARRAY['photo-spot', 'free', 'neighborhood', 'instagram-worthy'], 'Iconic photo spot with Manhattan Bridge view, cobblestone streets, trendy cafes'),
(44, 'Chelsea Market', 'food', 25, 90, 4.5, '(40.742314, -74.006570)', ARRAY['food-hall', 'shopping', 'indoor', 'popular'], 'Trendy food hall in a historic building with diverse culinary options'),
(44, 'Hudson Yards & The Vessel', 'culture', 10, 75, 4.4, '(40.753524, -74.001777)', ARRAY['architecture', 'modern', 'photo-spot', 'shopping'], 'Modern development with unique climbable structure and luxury shopping'),
(44, 'Brooklyn Botanic Garden', 'nature', 18, 120, 4.7, '(40.669250, -73.963678)', ARRAY['garden', 'outdoor', 'peaceful', 'seasonal'], 'Beautiful 52-acre garden, especially stunning during cherry blossom season'),
(44, 'Museum of Ice Cream', 'culture', 39, 75, 4.3, '(40.740811, -74.002857)', ARRAY['interactive', 'instagram-worthy', 'dessert', 'family-friendly'], 'Viral interactive dessert museum with colorful photo opportunities'),
(44, 'Smorgasburg Williamsburg', 'food', 20, 90, 4.6, '(40.716911, -73.962997)', ARRAY['outdoor-market', 'food-vendors', 'weekend', 'trendy'], 'America''s largest weekly open-air food market with 100+ vendors'),
(44, 'Sleep No More', 'nightlife', 150, 180, 4.7, '(40.744946, -73.999242)', ARRAY['theater', 'immersive', 'unique', 'trending'], 'Immersive theater experience in a massive multi-story space'),
(44, 'Williamsburg Waterfront', 'nature', 0, 90, 4.6, '(40.719444, -73.962222)', ARRAY['waterfront', 'trendy', 'free', 'scenic-views'], 'Hip Brooklyn neighborhood with waterfront parks and stunning Manhattan views'),
(44, 'Color Factory', 'culture', 38, 90, 4.4, '(40.721181, -74.000523)', ARRAY['interactive', 'colorful', 'instagram-worthy', 'art'], 'Interactive art installation celebrating color with 16+ rooms'),
(44, 'Governors Island', 'nature', 0, 180, 4.7, '(40.689169, -74.017014)', ARRAY['island', 'free', 'outdoor', 'seasonal'], 'Car-free island with parks, art installations, and stunning harbor views');

-- LOS ANGELES - Adding 12 more activities to reach 22 total
INSERT INTO activities (city_id, name, category, cost, duration, rating, coordinates, tags, description) VALUES
(40, 'The Getty Center', 'culture', 0, 150, 4.8, '(34.078056, -118.473889)', ARRAY['museum', 'free', 'architecture', 'gardens'], 'World-class art museum with stunning architecture, gardens, and city views'),
(40, 'Venice Canals', 'nature', 0, 45, 4.6, '(33.985556, -118.468889)', ARRAY['scenic', 'free', 'walkable', 'photo-spot'], 'Charming historic canals with beautiful homes and bridges'),
(40, 'Abbot Kinney Boulevard', 'shopping', 30, 120, 4.5, '(33.991667, -118.468889)', ARRAY['trendy', 'boutiques', 'cafes', 'art-galleries'], 'Hip street with trendy boutiques, galleries, and restaurants'),
(40, 'Griffith Observatory', 'culture', 0, 120, 4.7, '(34.118333, -118.300278)', ARRAY['free', 'science', 'views', 'iconic'], 'Free observatory with planetarium shows and iconic LA views'),
(40, 'The Broad Museum', 'culture', 0, 90, 4.7, '(34.054444, -118.250556)', ARRAY['contemporary-art', 'free', 'instagram-worthy', 'museum'], 'Contemporary art museum featuring Yayoi Kusama''s Infinity Rooms'),
(40, 'Arts District LA', 'culture', 0, 120, 4.5, '(34.043333, -118.236389)', ARRAY['street-art', 'trendy', 'free', 'neighborhood'], 'Vibrant neighborhood with stunning murals, galleries, and cafes'),
(40, 'The Last Bookstore', 'culture', 0, 60, 4.6, '(34.046111, -118.256111)', ARRAY['books', 'instagram-worthy', 'indoor', 'unique'], 'Massive independent bookstore with famous book tunnels and art installations'),
(40, 'Manhattan Beach Pier', 'beaches', 0, 90, 4.6, '(33.884722, -118.410000)', ARRAY['beach', 'free', 'surfing', 'outdoor'], 'Beautiful beach with pier, great for sunsets and volleyball'),
(40, 'Runyon Canyon', 'nature', 0, 90, 4.4, '(34.112222, -118.352222)', ARRAY['hiking', 'free', 'views', 'dog-friendly'], 'Popular hiking trail with panoramic city views and celebrity sightings'),
(40, 'Museum of Ice Cream LA', 'culture', 39, 75, 4.3, '(34.065278, -118.360833)', ARRAY['interactive', 'dessert', 'instagram-worthy', 'family-friendly'], 'Viral interactive museum with colorful installations and unlimited ice cream'),
(40, 'Grand Central Market', 'food', 20, 75, 4.5, '(34.050556, -118.249444)', ARRAY['food-hall', 'diverse', 'historic', 'popular'], 'Historic downtown food hall with diverse vendors and trendy eateries'),
(40, 'Melrose Trading Post', 'shopping', 5, 90, 4.4, '(34.083889, -118.349444)', ARRAY['flea-market', 'vintage', 'weekend', 'outdoor'], 'Sunday flea market with vintage finds, local artisans, and food trucks');

-- CHICAGO - Adding 12 more activities to reach 22 total
INSERT INTO activities (city_id, name, category, cost, duration, rating, coordinates, tags, description) VALUES
(18, 'Navy Pier', 'culture', 0, 120, 4.4, '(41.891667, -87.605000)', ARRAY['waterfront', 'family-friendly', 'entertainment', 'iconic'], 'Iconic pier with Ferris wheel, restaurants, and lake views'),
(18, 'Millennium Park & Cloud Gate', 'culture', 0, 60, 4.8, '(41.882611, -87.623111)', ARRAY['free', 'photo-spot', 'iconic', 'art'], 'Famous "Bean" sculpture and outdoor art installations in downtown park'),
(18, '360 CHICAGO Observation Deck', 'culture', 30, 75, 4.6, '(41.898611, -87.623056)', ARRAY['views', 'observation-deck', 'indoor', 'iconic'], 'Skydeck on 94th floor with TILT glass platform experience'),
(18, 'The Art Institute of Chicago', 'culture', 32, 180, 4.8, '(41.879722, -87.623889)', ARRAY['museum', 'world-class', 'indoor', 'art'], 'One of the oldest and largest art museums in the United States'),
(18, 'Riverwalk Chicago', 'nature', 0, 90, 4.7, '(41.887778, -87.621111)', ARRAY['waterfront', 'free', 'walkable', 'scenic'], 'Beautiful pedestrian waterfront with restaurants and boat tours'),
(18, 'Wrigley Field', 'culture', 50, 180, 4.7, '(41.948333, -87.655556)', ARRAY['baseball', 'historic', 'sports', 'iconic'], 'Historic baseball stadium, home of the Chicago Cubs since 1914'),
(18, 'Chicago Riverwalk Architecture Tour', 'culture', 45, 90, 4.9, '(41.887778, -87.621111)', ARRAY['boat-tour', 'architecture', 'educational', 'popular'], 'Famous architectural boat tour showcasing Chicago''s skyline'),
(18, 'Lincoln Park', 'nature', 0, 120, 4.6, '(41.921944, -87.633889)', ARRAY['park', 'free', 'outdoor', 'large'], 'Large lakefront park with zoo, conservatory, and beaches'),
(18, 'The 606 Trail', 'nature', 0, 75, 4.6, '(41.913333, -87.680278)', ARRAY['elevated-trail', 'free', 'biking', 'urban'], 'Elevated trail built on old railway line through neighborhoods'),
(18, 'Chicago Theatre', 'culture', 40, 120, 4.7, '(41.885278, -87.627778)', ARRAY['theater', 'historic', 'entertainment', 'iconic'], 'Iconic theater with famous marquee sign, offering tours and shows'),
(18, 'Museum of Science and Industry', 'culture', 25, 180, 4.6, '(41.790833, -87.583056)', ARRAY['science', 'interactive', 'family-friendly', 'large'], 'Massive science museum with interactive exhibits and real U-505 submarine'),
(18, 'Maggie Daley Park', 'nature', 0, 90, 4.7, '(41.882222, -87.619444)', ARRAY['park', 'family-friendly', 'playground', 'free'], 'Modern park with unique playground, climbing walls, and skating ribbon');

-- MIAMI - Adding 20 activities (new city with 0)
INSERT INTO activities (city_id, name, category, cost, duration, rating, coordinates, tags, description) VALUES
-- First get Miami's city_id
-- Assuming we need to add Miami first if it doesn't exist

-- LAS VEGAS - Adding 20 activities (new city with 0)
-- Similar approach

-- PARIS - Already has 22, might add a few more trending ones

-- TOKYO - Already has 20, should add 2-3 more

-- Let's continue with cities that need activities
