-- Practice Database Schema
-- This is a simple database to help you get familiar with PostgreSQL and Docker

-- Companies table
CREATE TABLE companies (
    company_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contacts table
CREATE TABLE contacts (
    contact_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    company_id INTEGER REFERENCES companies(company_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample companies
INSERT INTO companies (name, industry) VALUES
    ('Acme Corporation', 'Technology'),
    ('Global Industries', 'Manufacturing'),
    ('Sunrise Consulting', 'Consulting'),
    ('Pacific Trading Co', 'Retail'),
    ('Mountain Software', 'Technology');

-- Insert sample contacts
INSERT INTO contacts (first_name, last_name, email, phone, company_id) VALUES
    ('John', 'Smith', 'john.smith@acme.com', '555-123-4567', 1),
    ('Jane', 'Doe', 'jane.doe@global.com', '555-234-5678', 2),
    ('Robert', 'Johnson', 'rjohnson@sunrise.com', '555-345-6789', 3),
    ('Emily', 'Williams', 'emily.w@pacific.com', '555-456-7890', 4),
    ('Michael', 'Brown', 'mbrown@mountain.com', '555-567-8901', 5),
    ('Sarah', 'Davis', 'sarah.davis@acme.com', '555-678-9012', 1),
    ('David', 'Miller', 'dmiller@global.com', NULL, 2),
    ('Lisa', 'Wilson', NULL, '555-789-0123', 3);

-- Create a simple view for practice
CREATE VIEW contact_directory AS
SELECT
    c.first_name || ' ' || c.last_name AS full_name,
    c.email,
    c.phone,
    co.name AS company_name
FROM contacts c
LEFT JOIN companies co ON c.company_id = co.company_id;
