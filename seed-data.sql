-- Property Maintenance Agent - Seed Data
-- Sample data for development and testing
-- Using proper UUID format

-- ============================================================================
-- PROPERTIES (1 property)
-- ============================================================================
INSERT INTO properties (id, name, address, pm_chat_id) VALUES
    ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Meridian Apartments', '123 Main Street, Detroit MI', '@meridian_pm_alerts');

-- ============================================================================
-- UNITS (10 units with tenants)
-- All units belong to Meridian Apartments (property_id: a1b2c3d4-e5f6-7890-abcd-ef1234567890)
-- ============================================================================
INSERT INTO units (id, property_id, unit_number, tenant_name, tenant_phone, is_active) VALUES
    ('11111111-1111-1111-1111-111111111101', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '1A', 'John Smith', '+15551234567', true),
    ('11111111-1111-1111-1111-111111111102', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '1B', 'Maria Garcia', '+15551234568', true),
    ('11111111-1111-1111-1111-111111111103', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '2A', 'Robert Johnson', '+15551234569', true),
    ('11111111-1111-1111-1111-111111111104', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '2B', 'Emily Davis', '+15551234570', true),
    ('11111111-1111-1111-1111-111111111105', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '3A', 'Michael Brown', '+15551234571', true),
    ('11111111-1111-1111-1111-111111111106', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '3B', 'Sarah Wilson', '+15551234572', true),
    ('11111111-1111-1111-1111-111111111107', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '4A', 'David Miller', '+15551234573', true),
    ('11111111-1111-1111-1111-111111111108', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '4B', 'Jennifer Taylor', '+15551234574', true),
    ('11111111-1111-1111-1111-111111111109', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '5A', 'Christopher Anderson', '+15551234575', true),
    ('11111111-1111-1111-1111-111111111110', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '5B', 'Amanda Thomas', '+15551234576', true);

-- ============================================================================
-- VENDORS (3 vendors by trade type)
-- ============================================================================
INSERT INTO vendors (id, trade_type, company_name, contact_name, phone, is_active) VALUES
    ('33333333-3333-3333-3333-333333333301', 'HVAC', 'Cool Breeze HVAC', 'Mike Reynolds', '+15559876543', true),
    ('33333333-3333-3333-3333-333333333302', 'Plumbing', 'Quick Fix Plumbing', 'Sarah Martinez', '+15559876544', true),
    ('33333333-3333-3333-3333-333333333303', 'Electrical', 'Spark Electric Co', 'James Chen', '+15559876545', true);

-- ============================================================================
-- SAMPLE TICKETS (optional - for testing the workflow)
-- These demonstrate different statuses and trade types
-- ============================================================================
INSERT INTO tickets (id, unit, tenant_name, tenant_phone, issue_raw, urgency, trade_type, status, vendor_id, notes, channel) VALUES
    -- Sample HVAC ticket - dispatched to vendor
    ('44444444-4444-4444-4444-444444444401', '4B', 'Jennifer Taylor', '+15551234574', 'My AC is not working. The unit is making a weird noise and not cooling at all.', 'HIGH', 'HVAC', 'dispatched', '33333333-3333-3333-3333-333333333301', '[2026-04-17 09:00] Ticket received via SMS
[2026-04-17 09:05] Triaged as HVAC - HIGH urgency
[2026-04-17 09:10] Dispatched to Cool Breeze HVAC', 'sms'),
    
    -- Sample plumbing ticket - triaged, awaiting dispatch
    ('44444444-4444-4444-4444-444444444402', '2A', 'Robert Johnson', '+15551234569', 'Kitchen sink is leaking under the cabinet. Water on the floor.', 'MEDIUM', 'Plumbing', 'triaged', NULL, '[2026-04-17 08:30] Ticket received via voice
[2026-04-17 08:35] Triaged as Plumbing - MEDIUM urgency', 'voice'),
    
    -- Sample electrical ticket - incoming, not yet triaged
    ('44444444-4444-4444-4444-444444444403', '1A', 'John Smith', '+15551234567', 'One of the outlets in my bedroom is sparking when I plug things in.', 'EMERGENCY', 'Electrical', 'incoming', NULL, '[2026-04-17 09:15] Ticket received via web portal', 'web'),
    
    -- Sample completed ticket - for testing closed workflow
    ('44444444-4444-4444-4444-444444444404', '3A', 'Michael Brown', '+15551234571', 'Door lock is stuck and won''t turn properly.', 'LOW', 'General', 'completed', NULL, '[2026-04-16 14:00] Ticket received
[2026-04-16 14:30] Maintenance staff dispatched
[2026-04-16 15:00] Lock lubricated and fixed', 'sms');
