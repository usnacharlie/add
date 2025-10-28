-- Migration: Add USSD PIN fields to members table
-- Date: 2025-01-11
-- Description: Add PIN authentication fields for USSD security

-- Add PIN hash column
ALTER TABLE members ADD COLUMN IF NOT EXISTS ussd_pin_hash VARCHAR(255);

-- Add PIN attempts tracking
ALTER TABLE members ADD COLUMN IF NOT EXISTS pin_attempts INTEGER DEFAULT 0;

-- Add PIN lock timestamp
ALTER TABLE members ADD COLUMN IF NOT EXISTS pin_locked_until TIMESTAMP;

-- Add index for faster PIN verification lookups
CREATE INDEX IF NOT EXISTS idx_members_pin_locked ON members(pin_locked_until);

-- Comment on columns
COMMENT ON COLUMN members.ussd_pin_hash IS '4-digit PIN hash for USSD authentication';
COMMENT ON COLUMN members.pin_attempts IS 'Track failed PIN attempts (locks after 3 attempts)';
COMMENT ON COLUMN members.pin_locked_until IS 'Account locked until this timestamp';
