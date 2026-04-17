"""
Property Maintenance Agent - Database Layer
Supabase connection and helper functions for ticket management.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime
from supabase import create_client, Client


# ============================================================================
# SUPABASE CONNECTION
# ============================================================================

def get_supabase_client() -> Client:
    """
    Initialize and return Supabase client from environment variables.
    
    Uses service role key for internal API calls (full database access).
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables."
        )
    
    return create_client(supabase_url, supabase_key)


# Global client instance (initialized on first use)
_supabase_client: Optional[Client] = None


def get_db() -> Client:
    """Get or create the Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_supabase_client()
    return _supabase_client


# ============================================================================
# TICKET OPERATIONS
# ============================================================================

async def create_ticket(
    unit: str,
    issue_raw: str,
    channel: str,
    tenant_phone: Optional[str] = None,
    property_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new maintenance ticket in Supabase.
    
    Args:
        unit: Unit number (e.g., "101", "2B")
        issue_raw: Raw description of the maintenance issue
        channel: Intake channel ("sms", "call", or "web")
        tenant_phone: Tenant's phone number (optional)
        property_name: Property name (optional, can be extracted from unit)
    
    Returns:
        Dictionary containing the created ticket data including ID
    
    Raises:
        Exception: If ticket creation fails
    """
    client = get_db()
    
    # Prepare ticket data
    ticket_data = {
        "unit": unit,
        "issue_raw": issue_raw,
        "channel": channel,
        "status": "incoming",  # Initial status
        "tenant_phone": tenant_phone,
        "property": property_name,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    try:
        # Insert ticket into Supabase
        result = client.table("tickets").insert(ticket_data).execute()
        
        if not result.data or len(result.data) == 0:
            raise Exception("No data returned from Supabase after insert")
        
        ticket = result.data[0]
        print(f"Created ticket {ticket['id']} for unit {unit}")
        
        return ticket
        
    except Exception as e:
        print(f"Error creating ticket: {e}")
        raise


async def get_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a ticket by ID.
    
    Args:
        ticket_id: The UUID of the ticket to retrieve
    
    Returns:
        Dictionary containing ticket data, or None if not found
    """
    client = get_db()
    
    try:
        result = client.table("tickets").select("*").eq("id", ticket_id).execute()
        
        if not result.data or len(result.data) == 0:
            print(f"Ticket {ticket_id} not found")
            return None
        
        return result.data[0]
        
    except Exception as e:
        print(f"Error retrieving ticket {ticket_id}: {e}")
        raise


async def update_ticket(
    ticket_id: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Update a ticket by ID.
    
    Args:
        ticket_id: The UUID of the ticket to update
        updates: Dictionary of fields to update
    
    Returns:
        Dictionary containing updated ticket data, or None if not found
    """
    client = get_db()
    
    # Always update the updated_at timestamp
    updates["updated_at"] = datetime.utcnow().isoformat()
    
    try:
        result = client.table("tickets").update(updates).eq("id", ticket_id).execute()
        
        if not result.data or len(result.data) == 0:
            print(f"Ticket {ticket_id} not found for update")
            return None
        
        return result.data[0]
        
    except Exception as e:
        print(f"Error updating ticket {ticket_id}: {e}")
        raise


async def get_tickets_by_status(status: str) -> list[Dict[str, Any]]:
    """
    Retrieve all tickets with a specific status.
    
    Args:
        status: The status to filter by (e.g., "incoming", "triaged")
    
    Returns:
        List of ticket dictionaries
    """
    client = get_db()
    
    try:
        result = client.table("tickets").select("*").eq("status", status).execute()
        
        if not result.data:
            return []
        
        return result.data
        
    except Exception as e:
        print(f"Error retrieving tickets by status {status}: {e}")
        raise


async def get_unit(unit_number: str, property_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve a unit by number.
    
    Args:
        unit_number: The unit number to look up
        property_id: Optional property ID for more specific lookup
    
    Returns:
        Dictionary containing unit data, or None if not found
    """
    client = get_db()
    
    try:
        query = client.table("units").select("*").eq("unit_number", unit_number)
        
        if property_id:
            query = query.eq("property_id", property_id)
        
        result = query.execute()
        
        if not result.data or len(result.data) == 0:
            return None
        
        return result.data[0]
        
    except Exception as e:
        print(f"Error retrieving unit {unit_number}: {e}")
        raise


async def get_vendors_by_trade(trade: str) -> list[Dict[str, Any]]:
    """
    Retrieve active vendors by trade type.
    
    Args:
        trade: The trade type (HVAC, Plumbing, Electrical, General, Other)
    
    Returns:
        List of vendor dictionaries
    """
    client = get_db()
    
    try:
        result = (
            client.table("vendors")
            .select("*")
            .eq("trade", trade)
            .eq("active", True)
            .execute()
        )
        
        if not result.data:
            return []
        
        return result.data
        
    except Exception as e:
        print(f"Error retrieving vendors for trade {trade}: {e}")
        raise
