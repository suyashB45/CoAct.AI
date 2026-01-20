-- Database Schema for CoAct AI

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE, -- Supports 'coactai' from Login default
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255), -- From Signup form
    role VARCHAR(100) DEFAULT 'user', -- Default for new signups
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default user matching Login.tsx state
INSERT INTO users (username, email, password_hash, full_name, role)
VALUES ('coactai', 'admin@coact.ai', 'coact@ai2026', 'Admin User', 'AI Product Developer 2')
ON CONFLICT (email) DO NOTHING;

-- 2. Practice History Table
-- Links a user's session to their specific scenario run
CREATE TABLE IF NOT EXISTS practice_history (
    session_id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scenario_type VARCHAR(50) NOT NULL, -- 'coaching', 'sales', 'learning', etc.
    role VARCHAR(100),
    ai_role VARCHAR(100),
    transcript JSONB,
    report_data JSONB,
    completed BOOLEAN DEFAULT FALSE
);

-- 3. Coaching Reports Table
-- Specific metrics for Coaching scenarios
CREATE TABLE IF NOT EXISTS coaching_reports (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES practice_history(session_id) ON DELETE CASCADE,
    overall_score FLOAT,
    empathy_score FLOAT,
    psych_safety_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Sales Reports Table
-- Specific metrics for Sales scenarios
CREATE TABLE IF NOT EXISTS sales_reports (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES practice_history(session_id) ON DELETE CASCADE,
    rapport_building_score FLOAT,
    value_articulation_score FLOAT,
    objection_handling_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Learning Plans Table
-- Qualitative feedback and personal growth data
CREATE TABLE IF NOT EXISTS learning_plans (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES practice_history(session_id) ON DELETE CASCADE,
    skill_focus_areas TEXT,
    practice_suggestions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
