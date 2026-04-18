-- Add write policies for the dashboard to update tickets
CREATE POLICY "Allow public update access to tickets" 
ON tickets FOR UPDATE 
USING (true);

CREATE POLICY "Allow public insert access to tickets" 
ON tickets FOR INSERT 
WITH CHECK (true);
