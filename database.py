"""
Property Maintenance Agent - Database Layer
PostgreSQL connection and helper functions for ticket management.
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncpg


# ============================================================================
# POSTGRESQL CONNECTION (Railway)
# ============================================================================

# Global connection pool (initialized on first use)
# Singleton pattern ensures efficient connection pooling across all requests
_db_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """
    Get or create the PostgreSQL connection pool.
    
    Uses Railway's DATABASE_URL environment variable (provided automatically).
    Connection pooling ensures efficient reuse of database connections.
    
    Returns:
        asyncpg connection pool instance
    """
    global _db_pool
    if _db_pool is None:
        database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            raise ValueError(
                "Missing DATABASE_URL environment variable. "
                "Railway provides this automatically when PostgreSQL is added."
            )
        
        # Create connection pool (5-10 connections is typical for web apps)
        _db_pool = await asyncpg.create_pool(
            dsn=database_url,
            minimum_size=3,
            maximum_size=10,
            command_timeout=60
        )
        print(f"[Database] Initialized PostgreSQL connection pool (3-10 connections)")
    
    return _db_pool


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
    Create a new maintenance ticket in PostgreSQL.
    
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
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO tickets (
                    unit, issue_raw, channel, status,
                    tenant_phone, urgency, trade_type
                )
                VALUES ($1, $2, $3, 'incoming', $4, 'MEDIUM', 'General')
                RETURNING *
                """,
                unit, issue_raw, channel, tenant_phone
            )
            
            if not row:
                raise Exception("No data returned after ticket insert")
            
            # Convert Row to dict for compatibility
            ticket = dict(row)
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
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM tickets WHERE id = $1",
                ticket_id
            )
            
            if not row:
                print(f"Ticket {ticket_id} not found")
                return None
            
            return dict(row)
            
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
    pool = await get_db_pool()
    
    # Always update the updated_at timestamp
    updates["updated_at"] = datetime.utcnow().isoformat()
    
    try:
        async with pool.acquire() as conn:
            # Build dynamic UPDATE query
            keys = list(updates.keys())
            values = list(updates.values())
            
            # Remove ticket_id from update if present (it's the WHERE clause)
            if "id" in keys:
                keys.remove("id")
                values.pop(keys.index("id") if "id" in [k for k in keys] else 0)
            
            set_clause = ", ".join([f"{key} = ${i+1}" for i, key in enumerate(keys)])
            
            row = await conn.fetchrow(
                f"""
                UPDATE tickets 
                SET {set_clause}
                WHERE id = ${len(values) + 1}
                RETURNING *
                """,
                *values, ticket_id
            )
            
            if not row:
                print(f"Ticket {ticket_id} not found for update")
                return None
            
            return dict(row)
            
    except Exception as e:
        print(f"Error updating ticket {ticket_id}: {e}")
        raise


async def get_tickets_by_status(status: str) -> List[Dict[str, Any]]:
    """
    Retrieve all tickets with a specific status.
    
    Args:
        status: The status to filter by (e.g., "incoming", "triaged")
    
    Returns:
        List of ticket dictionaries
    """
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM tickets WHERE status = $1 ORDER BY created_at DESC",
                status
            )
            
            if not rows:
                return []
            
            return [dict(row) for row in rows]
            
    except Exception as e:
        print(f"Error retrieving tickets by status {status}: {e}")
        raise


async def get_all_tickets() -> List[Dict[str, Any]]:
    """
    Retrieve all tickets ordered by creation date.
    
    Returns:
        List of ticket dictionaries
    """
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM tickets ORDER BY created_at DESC"
            )
            
            if not rows:
                return []
            
            return [dict(row) for row in rows]
            
    except Exception as e:
        print(f"Error retrieving all tickets: {e}")
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
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            if property_id:
                row = await conn.fetchrow(
                    "SELECT * FROM units WHERE unit_number = $1 AND property_id = $2",
                    unit_number, property_id
                )
            else:
                row = await conn.fetchrow(
                    "SELECT * FROM units WHERE unit_number = $1",
                    unit_number
                )
            
            if not row:
                return None
            
            return dict(row)
            
    except Exception as e:
        print(f"Error retrieving unit {unit_number}: {e}")
        raise


async def get_vendors_by_trade(trade: str) -> List[Dict[str, Any]]:
    """
    Retrieve active vendors by trade type.
    
    Args:
        trade: The trade type (HVAC, Plumbing, Electrical, General, Other)
    
    Returns:
        List of vendor dictionaries
    """
    pool = await get_db_pool()
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM vendors WHERE trade_type = $1 AND is_active = TRUE",
                trade
            )
            
            if not rows:
                return []
            
            return [dict(row) for row in rows]
            
    except Exception as e:
        print(f"Error retrieving vendors for trade {trade}: {e}")
        raise
