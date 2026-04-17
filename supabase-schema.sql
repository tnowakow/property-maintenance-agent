-- Property Maintenance Agent - Supabase Database Schema
-- This schema supports the automated property maintenance ticketing system

-- ============================================================================
-- PROPERTIES TABLE
-- Stores information about managed properties (apartment buildings, complexes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,              -- e.g., "Meridian Apartments"
    address TEXT,                    -- Full street address
    pm_chat_id TEXT,                 -- Telegram chat ID for property manager alerts
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE properties IS 'Stores property/complex information including Telegram integration';
COMMENT ON COLUMN properties.pm_chat_id IS 'Telegram chat ID where maintenance alerts are sent';

-- ============================================================================
-- UNITS TABLE
-- Stores individual units within properties with tenant contact info
-- ============================================================================
CREATE TABLE IF NOT EXISTS units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    unit_number TEXT NOT NULL,       -- e.g., "4B", "Apt 12"
    tenant_name TEXT,                -- Current tenant name
    tenant_phone TEXT,               -- Tenant phone number for SMS/voice
    is_active BOOLEAN DEFAULT TRUE,  -- Whether unit is currently occupied/active
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE units IS 'Individual rental units with tenant contact information';
COMMENT ON COLUMN units.unit_number IS 'Unit identifier as displayed to tenants (e.g., "4B")';

-- ============================================================================
-- VENDORS TABLE
-- Stores vendor/contractor information by trade type
-- ============================================================================
CREATE TABLE IF NOT EXISTS vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_type TEXT NOT NULL,        -- HVAC, Plumbing, Electrical, General
    company_name TEXT NOT NULL,      -- Vendor business name
    contact_name TEXT,               -- Primary contact person
    phone TEXT NOT NULL,             -- Contact phone number
    is_active BOOLEAN DEFAULT TRUE,  -- Whether vendor is currently available
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE vendors IS 'Vendor/contractor database organized by trade type';
COMMENT ON COLUMN vendors.trade_type IS 'Type of work: HVAC, Plumbing, Electrical, General';

-- ============================================================================
-- TICKETS TABLE
-- Core table for maintenance requests/tickets
-- ============================================================================
CREATE TABLE IF NOT EXISTS tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit TEXT NOT NULL,              -- Unit identifier (denormalized for quick access)
    tenant_name TEXT,                -- Tenant name at time of ticket creation
    tenant_phone TEXT,               -- Tenant phone for callbacks
    issue_raw TEXT NOT NULL,         -- Original submission text from tenant
    urgency TEXT NOT NULL,           -- LOW, MEDIUM, HIGH, EMERGENCY
    trade_type TEXT NOT NULL,        -- HVAC, Plumbing, Electrical, General, Other
    status TEXT NOT NULL,            -- incoming, triaged, dispatched, completed, closed
    vendor_id UUID REFERENCES vendors(id),  -- Assigned vendor (nullable until dispatch)
    notes TEXT,                      -- Agent actions log / internal notes
    channel TEXT,                    -- sms, voice, web - how ticket was submitted
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE tickets IS 'Maintenance request tickets with full lifecycle tracking';
COMMENT ON COLUMN tickets.issue_raw IS 'Original text from tenant submission (preserved for context)';
COMMENT ON COLUMN tickets.urgency IS 'Priority level: LOW, MEDIUM, HIGH, EMERGENCY';
COMMENT ON COLUMN tickets.status IS 'Workflow status: incoming -> triaged -> dispatched -> completed -> closed';
COMMENT ON COLUMN tickets.notes IS 'Chronological log of agent actions and vendor communications';

-- ============================================================================
-- INDEXES
-- Optimized for common query patterns in the maintenance workflow
-- ============================================================================

-- Tickets indexes (most queried table)
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at);
CREATE INDEX IF NOT EXISTS idx_tickets_unit ON tickets(unit);
CREATE INDEX IF NOT EXISTS idx_tickets_urgency ON tickets(urgency);
CREATE INDEX IF NOT EXISTS idx_tickets_trade_type ON tickets(trade_type);

-- Units indexes
CREATE INDEX IF NOT EXISTS idx_units_property_id ON units(property_id);
CREATE INDEX IF NOT EXISTS idx_units_unit_number ON units(unit_number);

-- Vendors indexes
CREATE INDEX IF NOT EXISTS idx_vendors_trade_type ON vendors(trade_type);
CREATE INDEX IF NOT EXISTS idx_vendors_is_active ON vendors(is_active);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- Note: RLS policies should be configured in the Supabase UI based on your
-- authentication setup. For a backend-only system, you may want to disable
-- RLS and use service role keys instead.
-- 
-- Example policy patterns to consider:
-- - Allow authenticated users to read/write tickets for their property
-- - Allow vendors to only see tickets assigned to them
-- - Admin users can access all data
-- ============================================================================
