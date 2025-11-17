-- Migration: Enforce one admin per college
-- This creates a unique partial index to ensure only one admin per college at database level

-- Create unique partial index: Only one user with 'admin' role per college
CREATE UNIQUE INDEX idx_one_admin_per_college 
ON users (college_id) 
WHERE role = 'admin';

-- This index will prevent:
-- 1. Multiple admins being created for the same college (at DB level)
-- 2. Race conditions where two admins could be created simultaneously
-- 3. Direct database manipulation bypassing API validation

-- Note: This is a partial index, so it only applies to rows where role = 'admin'
-- It allows multiple staff and student users per college, but only one admin
