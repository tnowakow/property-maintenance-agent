"""
Property Maintenance Agent - FastAPI Backend
Handles SMS, voice, and web intake for maintenance tickets.
"""

import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
import os
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import local modules
from models import (
    SMSIntakeRequest,
    VoiceIntakeRequest,
    WebIntakeRequest,
    TicketResponse,
    TicketCreateResponse,
    ProcessAgentRequest,
    ProcessAgentResponse,
)
from database import create_ticket, get_ticket, update_ticket, get_all_tickets, get_tickets_by_status

# Initialize FastAPI app
app = FastAPI(
    title="Property Maintenance Agent API",
    description="Backend for handling maintenance ticket intake via SMS, voice, and web forms",
    version="1.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Serve static frontend files (if built)
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), '..', 'dashboard-v2', 'dist')
if os.path.exists(FRONTEND_DIST):
    from fastapi.staticfiles import StaticFiles
    app.mount("/static", StaticFiles(directory=FRONTEND_DIST, html=True), name="static")
    print(f"[Startup] Frontend static files mounted at {FRONTEND_DIST}")
else:
    print(f"[Warning] Frontend dist not found at {FRONTEND_DIST} - API only mode")


@app.get("/")
async def root():
    """Health check endpoint - also serves frontend index.html if available."""
    # Try to serve frontend
    if os.path.exists(FRONTEND_DIST):
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
    
    # Fallback to API health check
    return {"status": "healthy", "service": "property-maintenance-agent"}


# ============================================================================
# INTAKE ENDPOINTS
# ============================================================================

@app.post("/intake/sms", response_model=TicketCreateResponse, status_code=status.HTTP_201_CREATED)
async def intake_sms(request: Request):
    """
    Twilio SMS webhook handler.
    
    Receives incoming SMS from tenants and creates a maintenance ticket.
    Twilio sends form-encoded data (application/x-www-form-urlencoded), not JSON.
    """
    # Parse form data from Twilio
    form = await request.form()
    logger.info(f"Raw Twilio form data: {dict(form)}")
    
    # Extract fields from form
    sender = form.get('From', '') or form.get('from', '')
    message = form.get('Body', '') or form.get('body', '')
    
    logger.info(f"Received SMS from {sender}: {message}")
    
    try:
        # Extract unit from message
        import re
        unit = None
        match = re.search(r'\bunit\s+(\d+[A-Z]?)\b', message, re.IGNORECASE)
        if match:
            unit = match.group(1)
        
        # Create ticket in Supabase with status="incoming"
        ticket = await create_ticket(
            unit=unit,
            issue_raw=message,
            channel="sms",
            tenant_phone=sender,
        )
        
        logger.info(f"Created ticket {ticket['id']} for unit {unit} from SMS")
        
        return TicketCreateResponse(
            status="success",
            ticket_id=ticket['id']
        )
    except Exception as e:
        logger.error(f"Error processing SMS intake: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to process SMS intake", "message": str(e)}
        )


@app.post("/intake/voice", response_model=TicketCreateResponse, status_code=status.HTTP_201_CREATED)
async def intake_voice(request: VoiceIntakeRequest):
    """
    Twilio voice transcript webhook handler.
    
    Receives transcribed voice messages from tenants and creates a maintenance ticket.
    """
    logger.info(f"Received voice transcription from {request.From}: {request.TranscriptionText}")
    
    try:
        # Create ticket in Supabase with status="incoming"
        ticket = await create_ticket(
            unit=request.get_unit(),  # Extract unit from message if present
            issue_raw=request.TranscriptionText,
            channel="call",
            tenant_phone=request.From,
        )
        
        logger.info(f"Created ticket {ticket.id} from voice call")
        
        return TicketCreateResponse(
            status="success",
            ticket_id=ticket.id
        )
    except Exception as e:
        logger.error(f"Error processing voice intake: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to process voice intake", "message": str(e)}
        )


@app.post("/intake/web", response_model=TicketCreateResponse, status_code=status.HTTP_201_CREATED)
async def intake_web(request: WebIntakeRequest):
    """
    Web form submission handler.
    
    Receives maintenance requests from the web form and creates a ticket.
    """
    logger.info(f"Received web form submission for unit {request.unit} from {request.name}")
    
    try:
        # Create ticket in Supabase with status="incoming"
        ticket = await create_ticket(
            unit=request.unit,
            issue_raw=request.issue,
            channel="web",
            tenant_phone=request.phone,
        )
        
        logger.info(f"Created ticket {ticket.id} from web form")
        
        return TicketCreateResponse(
            status="success",
            ticket_id=ticket.id,
            message=f"Thank you {request.name}! We've received your maintenance request. A technician will contact you within 4 hours."
        )
    except Exception as e:
        logger.error(f"Error processing web intake: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to process web form submission", "message": str(e)}
        )


# ============================================================================
# TICKET ENDPOINTS
# ============================================================================

@app.get("/ticket/{ticket_id}", response_model=TicketResponse)
async def get_ticket_endpoint(ticket_id: str):
    """
    Retrieve ticket by ID.
    
    Returns full ticket details including status, trade classification, and assigned vendor.
    """
    try:
        ticket = await get_ticket(ticket_id)
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Ticket not found", "ticket_id": ticket_id}
            )
        
        return TicketResponse.model_validate(ticket)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ticket {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to retrieve ticket", "message": str(e)}
        )


# ============================================================================
# DASHBOARD API ENDPOINTS (for frontend)
# ============================================================================

@app.get("/api/tickets")
async def list_tickets(
    status: Optional[str] = None,
    limit: int = 100
):
    """
    List all tickets with optional filtering.
    
    Args:
        status: Optional status filter (incoming, triaged, dispatched, etc.)
        limit: Maximum number of tickets to return (default 100)
    
    Returns:
        List of ticket dictionaries
    """
    try:
        if status:
            tickets = await get_tickets_by_status(status)
        else:
            tickets = await get_all_tickets()
        
        # Apply limit
        tickets = tickets[:limit]
        
        return {"tickets": tickets, "count": len(tickets)}
    except Exception as e:
        logger.error(f"Error listing tickets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to list tickets", "message": str(e)}
        )


@app.post("/api/tickets", response_model=TicketCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket_endpoint(request: WebIntakeRequest):
    """
    Create a new maintenance ticket via API.
    
    Used by the frontend dashboard for manual ticket creation.
    """
    logger.info(f"Creating ticket via API for unit {request.unit}")
    
    try:
        ticket = await create_ticket(
            unit=request.unit,
            issue_raw=request.issue,
            channel="web",
            tenant_phone=request.phone,
        )
        
        logger.info(f"Created ticket {ticket['id']} via API")
        
        return TicketCreateResponse(
            status="success",
            ticket_id=ticket['id'],
            message="Ticket created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to create ticket", "message": str(e)}
        )


@app.patch("/api/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket_endpoint(ticket_id: str, updates: dict):
    """
    Update a ticket by ID.
    
    Used by the frontend dashboard to update ticket status and fields.
    
    Args:
        ticket_id: The UUID of the ticket to update
        updates: Dictionary of fields to update (e.g., {"status": "triaged", "urgency": "HIGH"})
    
    Returns:
        Updated ticket data
    """
    logger.info(f"Updating ticket {ticket_id} with {updates}")
    
    try:
        # Validate that updates doesn't include 'id' (immutable)
        if "id" in updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Cannot update ticket ID", "message": "ID is immutable"}
            )
        
        updated_ticket = await update_ticket(ticket_id, updates)
        
        if not updated_ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Ticket not found", "ticket_id": ticket_id}
            )
        
        logger.info(f"Updated ticket {ticket_id} successfully")
        return TicketResponse.model_validate(updated_ticket)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ticket {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to update ticket", "message": str(e)}
        )


# ============================================================================
# AGENT ENDPOINTS
# ============================================================================

@app.post("/agent/process", response_model=ProcessAgentResponse)
async def process_agent(request: ProcessAgentRequest):
    """
    Trigger OpenClaw triage agent.
    
    This endpoint triggers the OpenClaw agent to process an incoming ticket.
    The agent will:
    - Classify urgency and trade type
    - Validate unit existence
    - Check for duplicates
    - Auto-dispatch to vendor
    - Send confirmation SMS and PM alerts
    
    NOTE: This is a placeholder implementation. In production, this would
    integrate with the OpenClaw skill system via HTTP or direct API call.
    """
    logger.info(f"Triggering agent processing for ticket {request.ticket_id}")
    
    try:
        # Placeholder: In production, this would call the OpenClaw triage agent
        # For now, we'll just update the ticket status to "triaged"
        
        await update_ticket(
            ticket_id=request.ticket_id,
            updates={
                "status": "triaged",
                "notes": f"Agent processing triggered at {datetime.utcnow().isoformat()}"
            }
        )
        
        logger.info(f"Ticket {request.ticket_id} marked for agent processing")
        
        return ProcessAgentResponse(
            status="success",
            message=f"Agent processing initiated for ticket {request.ticket_id}"
        )
    except Exception as e:
        logger.error(f"Error triggering agent process for ticket {request.ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to trigger agent processing", "message": str(e)}
        )


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "message": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))


# ============================================================================
# SPA FALLBACK ROUTE (must be last due to path matching)
# ============================================================================

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """
    Serve React SPA for any non-API route.
    Returns index.html to let React Router handle client-side routing.
    """
    # Don't interfere with API routes
    if full_path.startswith("api/") or full_path in ["intake", "agent", "health"]:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Serve frontend index.html
    if os.path.exists(FRONTEND_DIST):
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
    
    raise HTTPException(status_code=404, detail="Frontend not available")
