"""
Property Maintenance Agent - Pydantic Models
Request and response models for API validation.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import re


# ============================================================================
# INTAKE REQUEST MODELS
# ============================================================================

class SMSIntakeRequest(BaseModel):
    """
    Twilio SMS webhook request model with validation.
    
    Fields received from Twilio when a tenant sends an SMS.
    Includes input sanitization and phone number validation.
    """
    From: Optional[str] = Field(None, description="Sender's phone number (E.164 format)")
    body: str = Field(..., min_length=1, max_length=160, description="Message content")
    Body: Optional[str] = Field(None, description="Message content (alternative casing)")
    
    model_config = {
        'populate_by_name': True,
        'extra': 'allow'  # Allow extra fields from Twilio
    }
    
    @field_validator('From')
    @classmethod
    def validate_phone(cls, v):
        """
        Validate phone number format (E.164 standard).
        
        Accepts formats like: +1234567890, +1-234-567-8900
        Rejects invalid formats or empty strings.
        """
        if not v:
            return v  # Allow None for optional field
        
        # Remove common separators for validation
        cleaned = re.sub(r'[\s\-\(\)\.]', '', v)
        
        # Check E.164 format: + followed by 7-15 digits
        if not re.match(r'^\+?\d{7,15}$', cleaned):
            raise ValueError(
                f'Invalid phone number format: {v}. Expected E.164 format (e.g., +1234567890)'
            )
        
        return v
    
    @field_validator('body', 'Body')
    @classmethod
    def sanitize_body(cls, v):
        """
        Sanitize message body to prevent XSS attacks.
        
        Removes HTML/XML tags and non-ASCII characters.
        Limits length to 160 characters (SMS standard).
        """
        if not v:
            raise ValueError('Message body cannot be empty')
        
        # Remove HTML/XML tags (XSS prevention)
        sanitized = re.sub(r'<[^>]+>', '', v)
        
        # Keep only ASCII characters and common punctuation
        sanitized = re.sub(r'[^a-zA-Z0-9\s.,!?\'"()-]', '', sanitized)
        
        # Strip whitespace
        sanitized = sanitized.strip()
        
        if not sanitized:
            raise ValueError('Message body is empty after sanitization')
        
        return sanitized[:160]  # Enforce SMS length limit
    
    @property
    def message_body(self) -> str:
        """Get the message body, handling both field names."""
        return self.body or self.Body or ""
    
    @property
    def sender_phone(self) -> str:
        """Get the sender's phone number."""
        return self.From or ""
    
    def get_unit(self) -> Optional[str]:
        """
        Attempt to extract unit number from message body.
        
        Simple heuristic: look for patterns like "Unit 101" or just a number at the start.
        This should be improved with better NLP in production.
        """
        import re
        
        # Try to find "Unit X" pattern
        match = re.search(r'\bunit\s+(\d+[A-Z]?)\b', self.Body, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Try to find a standalone number at the beginning (potential unit number)
        match = re.match(r'^(\d{1,4}[A-Z]?)\b', self.Body.strip())
        if match:
            potential_unit = match.group(1)
            # Only return if it looks like a unit number (not a phone number or date)
            if len(potential_unit) <= 5 and not potential_unit.isdigit() or len(potential_unit) < 7:
                return potential_unit
        
        return None


class VoiceIntakeRequest(BaseModel):
    """
    Twilio voice transcription webhook request model.
    
    Fields received from Twilio after transcribing a voice message.
    """
    From: str = Field(..., description="Caller's phone number (E.164 format)")
    TranscriptionText: str = Field(..., description="Transcribed text from voice message")
    
    def get_unit(self) -> Optional[str]:
        """
        Attempt to extract unit number from transcribed message.
        
        Similar logic to SMSIntakeRequest.get_unit().
        """
        import re
        
        # Try to find "Unit X" pattern
        match = re.search(r'\bunit\s+(\d+[A-Z]?)\b', self.TranscriptionText, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Try to find a standalone number at the beginning
        match = re.match(r'^(\d{1,4}[A-Z]?)\b', self.TranscriptionText.strip())
        if match:
            potential_unit = match.group(1)
            if len(potential_unit) <= 5 and not potential_unit.isdigit() or len(potential_unit) < 7:
                return potential_unit
        
        return None


class WebIntakeRequest(BaseModel):
    """
    Web form submission request model.
    
    Fields submitted from the tenant web form.
    """
    unit: str = Field(..., description="Unit number (e.g., '101', '2B')")
    name: str = Field(..., description="Tenant's full name")
    phone: str = Field(..., description="Tenant's phone number")
    issue: str = Field(..., description="Description of the maintenance issue")
    urgency: Optional[Literal["LOW", "MEDIUM", "HIGH", "EMERGENCY"]] = Field(
        default=None,
        description="Self-reported urgency level"
    )
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        """Basic phone number validation."""
        import re
        # Remove common separators
        cleaned = re.sub(r'[\s\-\(\)\.]', '', v)
        if not re.match(r'^\+?\d{7,15}$', cleaned):
            raise ValueError("Invalid phone number format")
        return cleaned


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class TicketCreateResponse(BaseModel):
    """Response for ticket creation endpoints."""
    status: str = Field(default="success", description="Operation status")
    ticket_id: str = Field(..., description="UUID of the created ticket")
    message: Optional[str] = Field(default=None, description="Optional message to display")


class TicketResponse(BaseModel):
    """Full ticket response model."""
    id: str = Field(..., description="Ticket UUID")
    unit: str = Field(..., description="Unit number")
    property: Optional[str] = Field(default=None, description="Property name")
    issue_raw: str = Field(..., description="Original issue description")
    issue_summary: Optional[str] = Field(
        default=None,
        description="AI-generated summary of the issue"
    )
    trade: Optional[Literal["HVAC", "Plumbing", "Electrical", "General", "Other"]] = Field(
        default=None,
        description="Classified trade type"
    )
    urgency: Optional[Literal["LOW", "MEDIUM", "HIGH", "EMERGENCY"]] = Field(
        default=None,
        description="Classified urgency level"
    )
    status: str = Field(..., description="Current ticket status")
    channel: str = Field(..., description="Intake channel (sms/call/web)")
    tenant_phone: Optional[str] = Field(default=None, description="Tenant's phone number")
    created_at: datetime = Field(..., description="Ticket creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    assigned_vendor_id: Optional[str] = Field(
        default=None,
        description="ID of assigned vendor"
    )
    notes: Optional[str] = Field(default=None, description="Internal notes")


class ProcessAgentRequest(BaseModel):
    """Request model for triggering agent processing."""
    ticket_id: str = Field(..., description="UUID of the ticket to process")


class ProcessAgentResponse(BaseModel):
    """Response for agent processing endpoint."""
    status: str = Field(default="success", description="Operation status")
    message: str = Field(..., description="Processing result message")


# ============================================================================
# INTERNAL MODELS (not exposed via API)
# ============================================================================

class TicketInternal(BaseModel):
    """Internal ticket model for database operations."""
    id: Optional[str] = Field(default=None, description="Ticket UUID")
    unit: str
    property: Optional[str] = None
    issue_raw: str
    issue_summary: Optional[str] = None
    trade: Optional[Literal["HVAC", "Plumbing", "Electrical", "General", "Other"]] = None
    urgency: Optional[Literal["LOW", "MEDIUM", "HIGH", "EMERGENCY"]] = None
    status: str = "incoming"
    channel: Literal["sms", "call", "web"]
    tenant_phone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_vendor_id: Optional[str] = None
    notes: Optional[str] = None
