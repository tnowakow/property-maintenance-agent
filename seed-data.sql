-- Property Maintenance Agent - Seed Data
-- Sample data for development and testing

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
    ('u1a-0000-0000-0000-000000000001', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '1A', 'John Smith', '+15551234567', true),
    ('u1b-0000-0000-0000-000000000002', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '1B', 'Maria Garcia', '+15551234568', true),
    ('u2a-0000-0000-0000-000000000003', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '2A', 'Robert Johnson', '+15551234569', true),
    ('u2b-0000-0000-0000-000000000004', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '2B', 'Emily Davis', '+15551234570', true),
    ('u3a-0000-0000-0000-000000000005', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '3A', 'Michael Brown', '+15551234571', true),
    ('u3b-0000-0000-0000-000000000006', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '3B', 'Sarah Wilson', '+15551234572', true),
    ('u4a-0000-0000-0000-000000000007', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '4A', 'David Miller', '+15551234573', true),
    ('u4b-0000-0000-0000-000000000008', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '4B', 'Jennifer Taylor', '+15551234574', true),
    ('u5a-0000-0000-0000-000000000009', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '5A', 'Christopher Anderson', '+15551234575', true),
    ('u5b-0000-0000-0000-000000000010', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', '5B', 'Amanda Thomas', '+15551234576', true);

-- ============================================================================
-- VENDORS (3 vendors by trade type)
-- ============================================================================
INSERT INTO vendors (id, trade_type, company_name, contact_name, phone, is_active) VALUES
    ('v-hvac-0000-0000-000000000001', 'HVAC', 'Cool Breeze HVAC', 'Mike Reynolds', '+15559876543', true),
    ('v-plumb-0000-0000-000000000002', 'Plumbing', 'Quick Fix Plumbing', 'Sarah Martinez', '+15559876544', true),
    ('v-elect-0000-0000-000000000003', 'Electrical', 'Spark Electric Co', 'James Chen', '+15559876545', true);

-- ============================================================================
-- SAMPLE TICKETS (optional - for testing the workflow)
-- These demonstrate different statuses and trade types
-- ============================================================================
INSERT INTO tickets (id, unit, tenant_name, tenant_phone, issue_raw, urgency, trade_type, status, vendor_id, notes, channel) VALUES
    -- Sample HVAC ticket - dispatched to vendor
    ('t-hvac-0000-0000-000000000001', '4B', 'Jennifer Taylor', '+15551234574', 'My AC is not working. The unit is making a weird noise and not cooling at all.', 'HIGH', 'HVAC', 'dispatched', 'v-hvac-0000-0000-000000000001', '[2026-04-17 09:00] Ticket received via SMS\n[2026-04-17 09:05] Triaged as HVAC - HIGH urgency\n[2026-04-17 09:10] Dispatched to Cool Breeze HVAC', 'sms'),
    
    -- Sample plumbing ticket - triaged, awaiting dispatch
    ('t-plumb-0000-0000-000000000002', '2A', 'Robert Johnson', '+15551234569', 'Kitchen sink is leaking under the cabinet. Water on the floor.', 'MEDIUM', 'Plumbing', 'triaged', NULL, '[2026-04-17 08:30] Ticket received via voice\n[2026-04-17 08:35] Triaged as Plumbing - MEDIUM urgency', 'voice'),
    
    -- Sample electrical ticket - incoming, not yet triaged
    ('t-elect-0000-0000-000000000003', '1A', 'John Smith', '+15551234567', 'One of the outlets in my bedroom is sparking when I plug things in.', 'EMERGENCY', 'Electrical', 'incoming', NULL, '[2026-04-17 09:15] Ticket received via web portal', 'web'),
    
    -- Sample completed ticket - for testing closed workflow
    ('t-general-0000-0000-000000000004', '3A', 'Michael Brown', '+15551234571', 'Door lock is stuck and won''t turn properly.', 'LOW', 'General', 'completed', NULL, '[2026-04-16 14:00] Ticket received\n[2026-04-16 14:30] Maintenance staff dispatched\n[2026-04-16 15:00] Lock lubricated and fixed', 'sms');

-- ============================================================================
-- VERIFICATION QUERIES (run these to confirm data loaded correctly)
-- Uncomment to verify after running seed script
-- ============================================================================
-- SELECT COUNT(*) as property_count FROM properties; -- Should return 1
-- SELECT COUNT(*) as unit_count FROM units; -- Should return 10
-- SELECT COUNT(*) as vendor_count FROM vendors; -- Should return 3
-- SELECT COUNT(*) as ticket_count FROM tickets; -- Should return 4 (sample tickets)
