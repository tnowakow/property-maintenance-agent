-- Enable RLS on tickets table (if not already enabled)
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;

-- Allow anonymous/public read access to all tickets
CREATE POLICY "Allow public read access to tickets" 
ON tickets FOR SELECT 
USING (true);

-- Also enable and allow reads on related tables for the dashboard
ALTER TABLE units ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read access to units" 
ON units FOR SELECT 
USING (true);

ALTER TABLE vendors ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read access to vendors" 
ON vendors FOR SELECT 
USING (true);

ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read access to properties" 
ON properties FOR SELECT 
USING (true);
