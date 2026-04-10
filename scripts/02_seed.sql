-- ──────────────────────────────────────────────
-- QueryMate AI — E-Commerce Demo Seed Data
-- ──────────────────────────────────────────────
-- ~2,000 rows across 8 tables.
-- Realistic distributions: orders skew recent,
-- ratings skew 4-5 stars, most orders have 1-3 items.

-- ── Categories (10 rows) ──
INSERT INTO categories (name, description) VALUES
('Electronics',     'Smartphones, laptops, tablets, and accessories'),
('Clothing',        'Men''s and women''s apparel'),
('Home & Kitchen',  'Furniture, appliances, and kitchen tools'),
('Books',           'Fiction, non-fiction, and technical books'),
('Sports',          'Equipment, apparel, and accessories'),
('Beauty',          'Skincare, makeup, and personal care'),
('Toys & Games',    'Board games, puzzles, and children''s toys'),
('Automotive',      'Car parts, tools, and accessories'),
('Garden',          'Plants, tools, and outdoor furniture'),
('Office Supplies', 'Stationery, printers, and desk accessories');

-- ── Customers (200 rows) ──
INSERT INTO customers (name, email, city, state, created_at) VALUES
('Alice Johnson',     'alice.johnson@email.com',     'San Francisco', 'CA', '2024-01-15'),
('Bob Smith',         'bob.smith@email.com',         'New York',      'NY', '2024-01-20'),
('Carol Williams',    'carol.williams@email.com',    'Chicago',       'IL', '2024-02-01'),
('David Brown',       'david.brown@email.com',       'Houston',       'TX', '2024-02-10'),
('Eva Martinez',      'eva.martinez@email.com',      'Phoenix',       'AZ', '2024-02-15'),
('Frank Davis',       'frank.davis@email.com',       'Philadelphia',  'PA', '2024-03-01'),
('Grace Wilson',      'grace.wilson@email.com',      'San Antonio',   'TX', '2024-03-10'),
('Henry Taylor',      'henry.taylor@email.com',      'San Diego',     'CA', '2024-03-15'),
('Iris Anderson',     'iris.anderson@email.com',     'Dallas',        'TX', '2024-03-20'),
('Jack Thomas',       'jack.thomas@email.com',       'San Jose',      'CA', '2024-04-01'),
('Karen Jackson',     'karen.jackson@email.com',     'Austin',        'TX', '2024-04-05'),
('Leo White',         'leo.white@email.com',         'Jacksonville',  'FL', '2024-04-10'),
('Mia Harris',        'mia.harris@email.com',        'Fort Worth',    'TX', '2024-04-15'),
('Noah Clark',        'noah.clark@email.com',        'Columbus',      'OH', '2024-04-20'),
('Olivia Lewis',      'olivia.lewis@email.com',      'Charlotte',     'NC', '2024-05-01'),
('Peter Robinson',    'peter.robinson@email.com',    'Indianapolis',  'IN', '2024-05-05'),
('Quinn Walker',      'quinn.walker@email.com',      'Seattle',       'WA', '2024-05-10'),
('Rachel Hall',       'rachel.hall@email.com',       'Denver',        'CO', '2024-05-15'),
('Sam Allen',         'sam.allen@email.com',         'Nashville',     'TN', '2024-05-20'),
('Tina Young',        'tina.young@email.com',        'Portland',      'OR', '2024-06-01'),
('Ursula King',       'ursula.king@email.com',       'Las Vegas',     'NV', '2024-06-05'),
('Victor Wright',     'victor.wright@email.com',     'Memphis',       'TN', '2024-06-10'),
('Wendy Lopez',       'wendy.lopez@email.com',       'Louisville',    'KY', '2024-06-15'),
('Xavier Hill',       'xavier.hill@email.com',       'Baltimore',     'MD', '2024-06-20'),
('Yara Scott',        'yara.scott@email.com',        'Milwaukee',     'WI', '2024-07-01'),
('Zach Green',        'zach.green@email.com',        'Albuquerque',   'NM', '2024-07-05'),
('Amy Adams',         'amy.adams@email.com',         'Tucson',        'AZ', '2024-07-10'),
('Ben Baker',         'ben.baker@email.com',         'Fresno',        'CA', '2024-07-15'),
('Cathy Carter',      'cathy.carter@email.com',      'Sacramento',    'CA', '2024-07-20'),
('Dan Edwards',       'dan.edwards@email.com',       'Mesa',          'AZ', '2024-08-01'),
('Ella Foster',       'ella.foster@email.com',       'Kansas City',   'MO', '2024-08-05'),
('Fred Garcia',       'fred.garcia@email.com',       'Atlanta',       'GA', '2024-08-10'),
('Gina Hernandez',    'gina.hernandez@email.com',    'Omaha',         'NE', '2024-08-15'),
('Hugo Irving',       'hugo.irving@email.com',       'Miami',         'FL', '2024-08-20'),
('Ida James',         'ida.james@email.com',         'Raleigh',       'NC', '2024-09-01'),
('Jim Kelly',         'jim.kelly@email.com',         'Minneapolis',   'MN', '2024-09-05'),
('Kim Lee',           'kim.lee@email.com',           'Tampa',         'FL', '2024-09-10'),
('Luke Morgan',       'luke.morgan@email.com',       'Pittsburgh',    'PA', '2024-09-15'),
('Mona Nelson',       'mona.nelson@email.com',       'Cincinnati',    'OH', '2024-09-20'),
('Nick Owens',        'nick.owens@email.com',        'Orlando',       'FL', '2024-10-01'),
('Opal Parker',       'opal.parker@email.com',       'St. Louis',     'MO', '2024-10-05'),
('Paul Quinn',        'paul.quinn@email.com',        'Cleveland',     'OH', '2024-10-10'),
('Rose Reed',         'rose.reed@email.com',         'Honolulu',      'HI', '2024-10-15'),
('Steve Sanders',     'steve.sanders@email.com',     'Anchorage',     'AK', '2024-10-20'),
('Tara Torres',       'tara.torres@email.com',       'Boise',         'ID', '2024-11-01'),
('Uma Vargas',        'uma.vargas@email.com',        'Richmond',      'VA', '2024-11-05'),
('Vince Ward',        'vince.ward@email.com',        'Spokane',       'WA', '2024-11-10'),
('Willa Xu',          'willa.xu@email.com',          'Des Moines',    'IA', '2024-11-15'),
('Xena York',         'xena.york@email.com',         'Birmingham',    'AL', '2024-11-20'),
('Yuri Zimmerman',    'yuri.zimmerman@email.com',    'Madison',       'WI', '2024-12-01');

-- Generate 150 more customers with a series
INSERT INTO customers (name, email, city, state, created_at)
SELECT
    'Customer_' || i,
    'customer' || i || '@email.com',
    (ARRAY['Boston','Detroit','Seattle','Denver','Miami','Atlanta','Phoenix','Portland','Austin','Chicago'])[1 + (i % 10)],
    (ARRAY['MA','MI','WA','CO','FL','GA','AZ','OR','TX','IL'])[1 + (i % 10)],
    '2024-01-01'::date + (i % 365) * interval '1 day'
FROM generate_series(51, 200) AS i;

-- ── Products (100 rows) ──
INSERT INTO products (name, category_id, price, stock_quantity, created_at) VALUES
-- Electronics
('iPhone 15 Pro',           1, 999.99,  50,  '2024-01-01'),
('MacBook Air M3',          1, 1299.99, 30,  '2024-01-05'),
('Samsung Galaxy S24',      1, 849.99,  45,  '2024-01-10'),
('Sony WH-1000XM5',        1, 349.99,  80,  '2024-01-15'),
('iPad Air',                1, 599.99,  60,  '2024-02-01'),
('AirPods Pro 2',           1, 249.99,  120, '2024-02-10'),
('Dell XPS 15',             1, 1499.99, 25,  '2024-02-15'),
('Google Pixel 8',          1, 699.99,  55,  '2024-03-01'),
('Nintendo Switch OLED',    1, 349.99,  70,  '2024-03-10'),
('Kindle Paperwhite',       1, 149.99,  100, '2024-03-15'),
-- Clothing
('Nike Air Max 90',         2, 129.99,  200, '2024-01-01'),
('Levi''s 501 Jeans',       2, 69.99,   150, '2024-01-10'),
('Patagonia Down Jacket',   2, 279.99,  40,  '2024-01-20'),
('Adidas Ultraboost',       2, 189.99,  90,  '2024-02-01'),
('North Face Fleece',       2, 149.99,  60,  '2024-02-15'),
('Columbia Rain Jacket',    2, 89.99,   75,  '2024-03-01'),
('Under Armour Shorts',     2, 34.99,   200, '2024-03-15'),
('New Balance 574',         2, 84.99,   110, '2024-04-01'),
('Champion Hoodie',         2, 54.99,   130, '2024-04-15'),
('Hanes T-Shirt Pack',      2, 19.99,   300, '2024-05-01'),
-- Home & Kitchen
('Instant Pot Duo',         3, 89.99,   85,  '2024-01-05'),
('Dyson V15 Vacuum',        3, 749.99,  20,  '2024-01-15'),
('KitchenAid Mixer',        3, 399.99,  35,  '2024-02-01'),
('Ninja Blender',           3, 119.99,  70,  '2024-02-15'),
('Cuisinart Coffee Maker',  3, 79.99,   95,  '2024-03-01'),
('Lodge Cast Iron Skillet',  3, 44.99,  120, '2024-03-15'),
('Roomba i7+',              3, 599.99,  25,  '2024-04-01'),
('Yeti Tumbler 30oz',       3, 34.99,   200, '2024-04-15'),
('Casper Pillow',           3, 65.99,   80,  '2024-05-01'),
('Brita Water Filter',      3, 29.99,   150, '2024-05-15'),
-- Books
('Atomic Habits',           4, 16.99,   300, '2024-01-01'),
('The Pragmatic Programmer', 4, 49.99,  60,  '2024-01-10'),
('Clean Code',              4, 39.99,   80,  '2024-01-20'),
('System Design Interview',  4, 35.99,  70,  '2024-02-01'),
('Designing Data Apps',     4, 44.99,   55,  '2024-02-15'),
('Python Crash Course',     4, 29.99,   120, '2024-03-01'),
('Sapiens',                 4, 18.99,   200, '2024-03-15'),
('Deep Work',               4, 15.99,   180, '2024-04-01'),
('The Art of War',          4, 9.99,    250, '2024-04-15'),
('Thinking Fast and Slow',  4, 17.99,   140, '2024-05-01'),
-- Sports
('Yeti Cooler 45',          5, 299.99,  40,  '2024-01-05'),
('Hydro Flask 32oz',        5, 44.99,   180, '2024-01-15'),
('Fitbit Charge 6',         5, 159.99,  65,  '2024-02-01'),
('Yoga Mat Premium',        5, 29.99,   200, '2024-02-15'),
('Resistance Bands Set',    5, 24.99,   150, '2024-03-01'),
('Dumbbell Set 50lb',       5, 149.99,  45,  '2024-03-15'),
('Running Shoes Gel',       5, 129.99,  80,  '2024-04-01'),
('Camping Tent 4-Person',   5, 199.99,  30,  '2024-04-15'),
('Bike Helmet',             5, 59.99,   90,  '2024-05-01'),
('Jump Rope Speed',         5, 14.99,   200, '2024-05-15'),
-- Beauty
('CeraVe Moisturizer',     6, 15.99,   250, '2024-01-01'),
('Olay Retinol 24',        6, 28.99,   120, '2024-01-15'),
('Neutrogena Sunscreen',   6, 11.99,   300, '2024-02-01'),
('Dyson Airwrap',           6, 599.99,  15,  '2024-02-15'),
('Revlon Hair Dryer',       6, 39.99,   100, '2024-03-01'),
('MAC Lipstick',            6, 21.99,   150, '2024-03-15'),
('Dove Body Wash',          6, 8.99,    400, '2024-04-01'),
('Oral-B Electric Brush',   6, 99.99,   70,  '2024-04-15'),
('Clinique Serum',          6, 34.99,   85,  '2024-05-01'),
('Bath & Body Works Set',   6, 39.99,   110, '2024-05-15'),
-- Toys & Games
('LEGO Star Wars Set',      7, 79.99,   60,  '2024-01-05'),
('Monopoly Classic',         7, 24.99,   120, '2024-01-15'),
('Rubik''s Cube',            7, 12.99,   200, '2024-02-01'),
('Nerf Blaster Elite',      7, 29.99,   90,  '2024-02-15'),
('Play-Doh Mega Pack',      7, 19.99,   150, '2024-03-01'),
('Hot Wheels Track Set',     7, 49.99,   70,  '2024-03-15'),
('Barbie Dreamhouse',        7, 199.99,  20,  '2024-04-01'),
('Pokemon Cards Booster',   7, 4.99,    500, '2024-04-15'),
('Board Game Catan',         7, 44.99,   65,  '2024-05-01'),
('Puzzle 1000 Piece',        7, 14.99,   110, '2024-05-15'),
-- Automotive
('Car Phone Mount',         8, 14.99,   200, '2024-01-01'),
('Dash Cam 4K',             8, 129.99,  55,  '2024-01-15'),
('Tire Pressure Gauge',     8, 9.99,    300, '2024-02-01'),
('Car Vacuum Portable',     8, 49.99,   80,  '2024-02-15'),
('LED Headlight Bulbs',     8, 39.99,   120, '2024-03-01'),
('Jumper Cables',           8, 29.99,   90,  '2024-03-15'),
('Car Seat Cover Set',      8, 59.99,   60,  '2024-04-01'),
('Air Freshener Pack',      8, 7.99,    400, '2024-04-15'),
('Windshield Wipers',       8, 24.99,   150, '2024-05-01'),
('Motor Oil 5W-30',         8, 27.99,   200, '2024-05-15'),
-- Garden
('Lawn Mower Electric',     9, 299.99,  25,  '2024-01-05'),
('Garden Hose 100ft',       9, 39.99,   80,  '2024-01-15'),
('Pruning Shears',          9, 19.99,   150, '2024-02-01'),
('Potting Soil 40lb',       9, 12.99,   200, '2024-02-15'),
('Solar Garden Lights',     9, 29.99,   100, '2024-03-01'),
('Bird Feeder Cedar',       9, 24.99,   70,  '2024-03-15'),
('Patio Umbrella 9ft',      9, 89.99,   35,  '2024-04-01'),
('Wheelbarrow Steel',       9, 79.99,   40,  '2024-04-15'),
('Compost Bin',             9, 49.99,   55,  '2024-05-01'),
('Raised Garden Bed',       9, 59.99,   45,  '2024-05-15'),
-- Office Supplies
('HP Printer LaserJet',    10, 199.99,  40,  '2024-01-01'),
('Sharpie Marker Set',     10, 12.99,   200, '2024-01-15'),
('Post-it Notes Mega',     10, 19.99,   180, '2024-02-01'),
('Ergonomic Mouse',        10, 49.99,   90,  '2024-02-15'),
('Standing Desk Mat',      10, 39.99,   60,  '2024-03-01'),
('File Cabinet 3-Drawer',  10, 149.99,  30,  '2024-03-15'),
('Stapler Heavy Duty',     10, 14.99,   120, '2024-04-01'),
('Desk Organizer',         10, 24.99,   100, '2024-04-15'),
('Whiteboard 4x3ft',       10, 79.99,   35,  '2024-05-01'),
('Paper Shredder',         10, 89.99,   25,  '2024-05-15');

-- ── Orders (500 rows) ──
INSERT INTO orders (customer_id, order_date, status, total_amount)
SELECT
    1 + (random() * 199)::int,
    '2024-01-01'::date + (random() * 450)::int * interval '1 day',
    (ARRAY['pending', 'confirmed', 'shipped', 'delivered', 'delivered', 'delivered', 'delivered', 'cancelled'])[1 + (random() * 7)::int],
    0
FROM generate_series(1, 500);

-- ── Order Items (800 rows, 1-3 items per order) ──
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT
    o.id,
    p.id,
    1 + (random() * 3)::int,
    p.price
FROM orders o
CROSS JOIN LATERAL (
    SELECT id, price FROM products ORDER BY random() LIMIT (1 + (random() * 2)::int)
) p;

-- ── Update order totals ──
UPDATE orders o SET total_amount = (
    SELECT COALESCE(SUM(oi.quantity * oi.unit_price), 0)
    FROM order_items oi WHERE oi.order_id = o.id
);

-- ── Reviews (300 rows, ratings skew toward 4-5) ──
INSERT INTO reviews (product_id, customer_id, rating, comment, created_at)
SELECT
    1 + (random() * 99)::int,
    1 + (random() * 199)::int,
    -- Skew: 60% chance of 4-5 stars
    CASE
        WHEN random() < 0.15 THEN 1 + (random() * 2)::int  -- 1-3 stars (15%)
        WHEN random() < 0.40 THEN 4                          -- 4 stars (25%)
        ELSE 5                                                -- 5 stars (60%)
    END,
    (ARRAY[
        'Great product, highly recommend!',
        'Good quality for the price.',
        'Exactly what I needed.',
        'Fast shipping, works perfectly.',
        'Decent but could be better.',
        'Not what I expected.',
        'Amazing quality!',
        'Would buy again.',
        'Perfect gift idea.',
        'Solid build quality.',
        'Works as advertised.',
        'Love it!',
        'Exceeded my expectations.',
        'Pretty good overall.',
        'Could use some improvements.',
        NULL
    ])[1 + (random() * 15)::int],
    '2024-01-15'::date + (random() * 400)::int * interval '1 day'
FROM generate_series(1, 300);

-- ── Shipping (400 rows, for delivered/shipped orders) ──
INSERT INTO shipping (order_id, carrier, tracking_number, shipped_date, delivered_date)
SELECT
    o.id,
    (ARRAY['UPS', 'FedEx', 'USPS', 'DHL'])[1 + (random() * 3)::int],
    'TRK' || LPAD((random() * 999999999)::bigint::text, 12, '0'),
    o.order_date + (1 + (random() * 3)::int) * interval '1 day',
    CASE
        WHEN o.status = 'delivered' THEN o.order_date + (3 + (random() * 7)::int) * interval '1 day'
        ELSE NULL
    END
FROM orders o
WHERE o.status IN ('shipped', 'delivered')
LIMIT 400;

-- ── Payments (500 rows, one per order) ──
INSERT INTO payments (order_id, payment_method, amount, status, paid_at)
SELECT
    o.id,
    (ARRAY['credit_card', 'credit_card', 'credit_card', 'debit_card', 'paypal', 'bank_transfer'])[1 + (random() * 5)::int],
    o.total_amount,
    CASE
        WHEN o.status = 'cancelled' THEN 'refunded'
        WHEN o.status = 'pending' THEN 'pending'
        ELSE 'completed'
    END,
    CASE
        WHEN o.status != 'pending' THEN o.order_date + interval '1 hour'
        ELSE NULL
    END
FROM orders o;
