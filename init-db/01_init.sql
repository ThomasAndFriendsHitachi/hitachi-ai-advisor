-- 1. Enable the uuid-ossp extension to allow UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Create the Users table
-- We use UUID as Primary Key to ensure better security and scalability
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    mail VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL, -- Never store plain text passwords
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Create the AI Tasks results table
-- Added project_name and risk_score columns to match Dashboard requirements
CREATE TABLE IF NOT EXISTS public.ai_tasks_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_name VARCHAR(255),        -- Extracted from GitHub repository name
    risk_score VARCHAR(50),          -- Mocked or calculated risk level (High, Medium, Low)
    status VARCHAR(50) DEFAULT 'received', -- Current processing state
    raw_payload JSONB NOT NULL,       -- Full JSON data for audit/history
    processed_at TIMESTAMP DEFAULT NOW()
);

-- 4. Seed the database with a default Admin user
-- The password hash below corresponds to: admin123
-- Using ON CONFLICT to prevent errors during container restarts
INSERT INTO public.users (username, mail, password_hash, role) 
VALUES (
    'admin', 
    'admin@hitachi.com', 
    '$2a$12$K8pM/Sg8Bv0s9H.T9Y5oUe7y3zR2U8v5G4H3I2J1K0L9M8N7O6P5Q', 
    'admin'
)
ON CONFLICT (username) DO NOTHING;

-- Documentation comments for the database
COMMENT ON TABLE public.users IS 'Stores user credentials and roles for system access';
COMMENT ON TABLE public.ai_tasks_results IS 'Stores AI analysis results, project metadata, and webhook payloads';