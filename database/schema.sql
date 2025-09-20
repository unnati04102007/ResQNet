-- =====================
-- Create All Tables First
-- =====================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'citizen',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Volunteers table
CREATE TABLE IF NOT EXISTS volunteers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    bio TEXT,
    location TEXT,
    availability TEXT DEFAULT 'available',
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Skills table
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- Volunteer Skills junction table
CREATE TABLE IF NOT EXISTS volunteer_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    volunteer_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    FOREIGN KEY (volunteer_id) REFERENCES volunteers (id),
    FOREIGN KEY (skill_id) REFERENCES skills (id),
    UNIQUE(volunteer_id, skill_id)
);

-- Disaster Reports table
CREATE TABLE IF NOT EXISTS disaster_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    disaster_type TEXT NOT NULL,
    severity INTEGER CHECK (severity BETWEEN 1 AND 5),
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Assignments table
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    volunteer_id INTEGER NOT NULL,
    status TEXT DEFAULT 'assigned',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES disaster_reports (id),
    FOREIGN KEY (volunteer_id) REFERENCES volunteers (id)
);

-- Resources table
CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    availability TEXT DEFAULT 'available'
);

-- Resource Requests table
CREATE TABLE IF NOT EXISTS resource_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    resource_id INTEGER NOT NULL,
    quantity_needed INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES disaster_reports (id),
    FOREIGN KEY (resource_id) REFERENCES resources (id)
);

-- Donations table
CREATE TABLE IF NOT EXISTS donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_status TEXT DEFAULT 'pending',
    donated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donor_id) REFERENCES users (id)
);

-- =====================
-- Insert Sample Data
-- =====================

-- Users
INSERT OR REPLACE INTO users (username, email, password, role) VALUES
('unnati', 'alice@example.com', '1234', 'citizen'),
('bob', 'bob@example.com', '1234', 'volunteer'),
('charlie', 'charlie@example.com', '1234', 'admin');

-- Volunteers (Bob is user_id=2)
INSERT OR IGNORE INTO volunteers (user_id, bio, location) VALUES
(2, 'Volunteer from Delhi, available for rescue operations', 'Delhi');

-- Skills
INSERT OR IGNORE INTO skills (name) VALUES 
('First Aid'),
('Rescue Operations'),
('Food Distribution');

-- Get the volunteer ID for Bob (should be 1 since he's the first volunteer)
-- Volunteer Skills (Bob has First Aid + Rescue Ops)
INSERT OR IGNORE INTO volunteer_skills (volunteer_id, skill_id) VALUES
(1, 1), -- Bob has First Aid
(1, 2); -- Bob has Rescue Operations

-- Disaster Reports (Alice reports a flood)
INSERT OR IGNORE INTO disaster_reports (user_id, title, description, disaster_type, severity) VALUES
(1, 'Bridge collapse', 'Bridge collapsed due to flood', 'flood', 4);

-- Assignments (Assign Bob to Alice's flood report)
INSERT OR IGNORE INTO assignments (report_id, volunteer_id, status) VALUES
(1, 1, 'assigned');

-- Resources
INSERT OR IGNORE INTO resources (type, quantity, availability) VALUES
('Water Bottles', 500, 'available'),
('Blankets', 200, 'available'),
('Medicines', 100, 'available');

-- Resource Requests (Flood needs water bottles and medicines)
INSERT OR IGNORE INTO resource_requests (report_id, resource_id, quantity_needed, status) VALUES
(1, 1, 50, 'pending'), -- Flood needs 50 water bottles
(1, 3, 20, 'pending'); -- Flood needs 20 medicines

-- Donations
INSERT OR IGNORE INTO donations (donor_id, amount, payment_status) VALUES
(3, 1000.00, 'completed'), -- Charlie (admin) donated
(1, 500.00, 'completed');  -- Alice donated

-- =====================
-- Verification Queries
-- =====================

-- Check all data was inserted correctly
SELECT 'Users:' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'Volunteers:', COUNT(*) FROM volunteers
UNION ALL
SELECT 'Skills:', COUNT(*) FROM skills
UNION ALL
SELECT 'Volunteer Skills:', COUNT(*) FROM volunteer_skills
UNION ALL
SELECT 'Disaster Reports:', COUNT(*) FROM disaster_reports
UNION ALL
SELECT 'Assignments:', COUNT(*) FROM assignments
UNION ALL
SELECT 'Resources:', COUNT(*) FROM resources
UNION ALL
SELECT 'Resource Requests:', COUNT(*) FROM resource_requests
UNION ALL
SELECT 'Donations:', COUNT(*) FROM donations;