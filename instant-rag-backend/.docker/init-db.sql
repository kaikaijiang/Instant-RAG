-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the database if it doesn't exist
-- Note: This is redundant as the database is created by Docker Compose,
-- but included for completeness
-- CREATE DATABASE instant_rag;
