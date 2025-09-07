-- ============================
-- Users Table
-- ============================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS disaster_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disaster_type TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT,
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================
-- Disaster Reports
-- ============================
CREATE TABLE disaster_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    location TEXT NOT NULL,
    description TEXT,
    image_url TEXT,
    verified INTEGER DEFAULT 0, -- 0 = not verified, 1 = verified
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================
-- Volunteers
-- ============================
CREATE TABLE volunteers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL, -- 1-to-1 with user
    location TEXT,
    availability INTEGER DEFAULT 1, -- 1 = available, 0 = not
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================
-- Skills
-- ============================
CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- VolunteerSkills (M:N between volunteers and skills)
CREATE TABLE volunteer_skills (
    volunteer_id INTEGER,
    skill_id INTEGER,
    PRIMARY KEY (volunteer_id, skill_id),
    FOREIGN KEY (volunteer_id) REFERENCES volunteers(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- ============================
-- Assignments (volunteer -> report)
-- ============================
CREATE TABLE assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    volunteer_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
    status TEXT CHECK(status IN ('pending', 'in_progress', 'completed')) DEFAULT 'pending',
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (volunteer_id) REFERENCES volunteers(id) ON DELETE CASCADE,
    FOREIGN KEY (report_id) REFERENCES disaster_reports(id) ON DELETE CASCADE
);

-- ============================
-- Resources
-- ============================
CREATE TABLE resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    available INTEGER DEFAULT 1 -- 1 = available, 0 = out of stock
);

-- Resource Requests
CREATE TABLE resource_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    resource_type TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES disaster_reports(id) ON DELETE CASCADE
);

-- ============================
-- Donations (💳 Online only)
-- ============================
CREATE TABLE donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id INTEGER NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    payment_method TEXT NOT NULL CHECK(payment_method IN ('credit_card', 'debit_card', 'upi', 'netbanking')),
    transaction_id TEXT UNIQUE NOT NULL, -- from payment gateway
    status TEXT NOT NULL CHECK(status IN ('pending', 'success', 'failed')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donor_id) REFERENCES users(id) ON DELETE CASCADE
);
cursor.execute("""
CREATE TABLE IF NOT EXISTS disaster_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disaster_type TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT,
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);