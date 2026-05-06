#!/usr/bin/env python3
"""
Property Maintenance Triage Agent

This agent processes incoming maintenance tickets and uses AI to classify them by:
- Urgency level (LOW, MEDIUM, HIGH, EMERGENCY)
- Trade type (HVAC, Plumbing, Electrical, General, Other)

Run via cron every 5 minutes to check for new "incoming" tickets.
"""

import os
import sys
from datetime import datetime
from typing import Optional
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from supabase import create_client, Client
except ImportError:
    print("Installing required packages...")
    os.system('pip install python-dotenv supabase')
    from supabase import create_client, Client

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://jmkwrxtxfkvydjmlrmya.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_SERVICE_ROLE_KEY not found in environment variables")
    sys.exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Urgency classification rules
URGENCY_KEYWORDS = {
    'EMERGENCY': [
        'emergency', 'urgent', 'asap', 'immediately', 'no heat', 'no hot water',
        'gas leak', 'smell gas', 'fire', 'electrical fire', 'sparking', 
        'frozen pipes', 'burst pipe', 'major leak', 'flooding', 'water everywhere',
        'exposed wires', 'shocking', 'carbon monoxide', 'no ac in summer',
        'security issue', 'broken lock', 'cant get in'
    ],
    'HIGH': [
        'leak', 'not working', 'broken', 'stopped working', 'not heating', 
        'not cooling', 'smell', 'mold', 'no water', 'toilet not flushing',
        'door not closing', 'window broken', 'ac not working', 'heater not working'
    ],
    'MEDIUM': [
        'repair', 'fix', 'replace', 'loose', 'squeaky', 'scratch', 'stain',
        'painting', 'cleaning', 'light bulb', 'outlet not working', 'switch'
    ],
    'LOW': [
        'question', 'inquiry', 'request', 'nice to have', 'cosmetic', 
        'minor', 'small', 'when you have time'
    ]
}

# Trade type classification rules
TRADE_KEYWORDS = {
    'HVAC': [
        'ac', 'air conditioning', 'heater', 'heating', 'hvac', 'thermostat',
        'furnace', 'boiler', 'vent', 'duct', 'cooling', 'heat pump',
        'no heat', 'not cooling', 'too hot', 'too cold'
    ],
    'Plumbing': [
        'leak', 'leaking', 'water', 'pipe', 'plumbing', 'toilet', 'sink',
        'drain', 'faucet', 'shower', 'bathtub', 'tub', 'garbage disposal',
        'disposal', 'sewer', 'valve', 'hydrant', 'hose bib', 'water heater'
    ],
    'Electrical': [
        'electric', 'electrical', 'outlet', 'socket', 'switch', 'light', 
        'wiring', 'wire', 'breaker', 'panel', 'fuse', 'power', 'spark',
        'shock', 'short circuit', 'ceiling fan'
    ],
    'General': [
        'door', 'lock', 'window', 'cabinet', 'appliance', 'refrigerator',
        'stove', 'oven', 'dishwasher', 'microwave', 'washer', 'dryer',
        'floor', 'wall', 'ceiling', 'painting', 'carpet', 'tile'
    ]
}


def classify_urgency(issue_text: str) -> str:
    """
    Classify the urgency level of a maintenance issue.
    
    Args:
        issue_text: The raw text description of the issue
        
    Returns:
        Urgency level: LOW, MEDIUM, HIGH, or EMERGENCY
    """
    text_lower = issue_text.lower()
    
    # Check each urgency level from highest to lowest
    for urgency, keywords in URGENCY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return urgency
    
    # Default to MEDIUM if no keywords match
    return 'MEDIUM'


def classify_trade_type(issue_text: str) -> str:
    """
    Classify the trade type needed for a maintenance issue.
    
    Args:
        issue_text: The raw text description of the issue
        
    Returns:
        Trade type: HVAC, Plumbing, Electrical, General, or Other
    """
    text_lower = issue_text.lower()
    
    # Count matches for each trade type
    trade_scores = {trade: 0 for trade in TRADE_KEYWORDS}
    
    for trade, keywords in TRADE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                trade_scores[trade] += 1
    
    # Return the trade with highest score, or 'Other' if no matches
    max_score = max(trade_scores.values())
    if max_score == 0:
        return 'Other'
    
    # Get all trades with the max score and pick the first one
    for trade, score in trade_scores.items():
        if score == max_score:
            return trade
    
    return 'Other'


def fetch_incoming_tickets() -> list:
    """
    Fetch all tickets with status 'incoming' from Supabase.
    
    Returns:
        List of ticket dictionaries
    """
    try:
        result = supabase.table('tickets').select('*').eq('status', 'incoming').execute()
        return result.data or []
    except Exception as e:
        print(f"Error fetching tickets: {e}")
        return []


def update_ticket(ticket_id: str, urgency: str, trade_type: str) -> bool:
    """
    Update a ticket with classified values and change status to 'triaged'.
    
    Args:
        ticket_id: The ID of the ticket to update
        urgency: Classified urgency level
        trade_type: Classified trade type
        
    Returns:
        True if successful, False otherwise
    """
    try:
        update_data = {
            'urgency_level': urgency,
            'trade_type': trade_type,
            'status': 'triaged',
            'updated_at': datetime.now().isoformat()
        }
        
        result = supabase.table('tickets').update(update_data).eq('id', ticket_id).execute()
        
        if result.data:
            print(f"✓ Updated ticket {ticket_id}: urgency={urgency}, trade_type={trade_type}")
            return True
        else:
            print(f"✗ Failed to update ticket {ticket_id}")
            return False
            
    except Exception as e:
        print(f"Error updating ticket {ticket_id}: {e}")
        return False


def process_tickets():
    """
    Main function to process all incoming tickets.
    """
    print(f"\n{'='*60}")
    print(f"Triage Agent Running - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Fetch incoming tickets
    tickets = fetch_incoming_tickets()
    
    if not tickets:
        print("No incoming tickets to process.")
        return
    
    print(f"Found {len(tickets)} incoming ticket(s) to triage.\n")
    
    # Process each ticket
    success_count = 0
    for ticket in tickets:
        print(f"Processing ticket {ticket['id']}...")
        print(f"  Unit: {ticket.get('unit_number', 'N/A')}")
        print(f"  Issue: {ticket.get('issue_raw', 'No description')[:100]}...")
        
        # Classify the ticket
        urgency = classify_urgency(ticket.get('issue_raw', ''))
        trade_type = classify_trade_type(ticket.get('issue_raw', ''))
        
        print(f"  Classified as: {trade_type} - {urgency}")
        
        # Update the ticket
        if update_ticket(ticket['id'], urgency, trade_type):
            success_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Triage Complete: {success_count}/{len(tickets)} tickets processed successfully")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    try:
        process_tickets()
    except KeyboardInterrupt:
        print("\nTriage agent stopped by user.")
    except Exception as e:
        print(f"\nError running triage agent: {e}")
        sys.exit(1)
