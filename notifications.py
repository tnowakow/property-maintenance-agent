"""
Property Maintenance Agent - Notification Services
Handles Telegram alerts to property managers and SMS responses to tenants.
"""

import os
import httpx
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# TELEGRAM NOTIFICATIONS
# ============================================================================

async def send_telegram_alert(
    ticket_id: str,
    unit_number: str,
    issue_raw: str,
    urgency: str,
    trade_type: str,
    pm_chat_id: Optional[str] = None,
) -> bool:
    """
    Send a Telegram alert to the property manager when a new ticket is created.
    
    Args:
        ticket_id: The ID of the created ticket
        unit_number: Unit number where issue occurred
        issue_raw: Raw description of the issue
        urgency: Urgency level (LOW, MEDIUM, HIGH, EMERGENCY)
        trade_type: Classified trade type
        pm_chat_id: Telegram chat ID for property manager (optional, uses env var if not provided)
    
    Returns:
        True if sent successfully, False otherwise
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = pm_chat_id or os.getenv("TELEGRAM_PM_CHAT_ID")
    
    if not bot_token or not chat_id:
        logger.warning("Telegram credentials not configured. Skipping alert.")
        return False
    
    # Determine emoji based on urgency
    urgency_emojis = {
        "EMERGENCY": "🚨",
        "HIGH": "⚠️",
        "MEDIUM": "📝",
        "LOW": "📋"
    }
    
    emoji = urgency_emojis.get(urgency, "📝")
    
    # Truncate issue if too long
    issue_display = issue_raw[:100] + "..." if len(issue_raw) > 100 else issue_raw
    
    # Format message
    message = f"""{emoji} New Maintenance Ticket

*Unit:* {unit_number or 'N/A'}
*Issue:* {issue_display}
*Urgency:* {urgency}
*Trade:* {trade_type}
*Status:* Incoming

🔖 *Ticket ID:* `{ticket_id[:8]}`"""
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                logger.info(f"Telegram alert sent for ticket {ticket_id}")
                return True
            else:
                logger.error(f"Failed to send Telegram alert: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error sending Telegram alert: {e}")
        return False


# ============================================================================
# SMS RESPONSES (Twilio)
# ============================================================================

async def send_sms_response(
    tenant_phone: str,
    ticket_id: str,
    unit_number: str,
    issue_raw: str,
    urgency: str,
) -> bool:
    """
    Send an SMS confirmation to the tenant when their ticket is created.
    
    Args:
        tenant_phone: Tenant's phone number
        ticket_id: The ID of the created ticket
        unit_number: Unit number where issue occurred
        issue_raw: Raw description of the issue
        urgency: Urgency level
    
    Returns:
        True if sent successfully, False otherwise
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    if not all([account_sid, auth_token, from_number]):
        logger.warning("Twilio credentials not configured. Skipping SMS response.")
        return False
    
    # Determine expected response time based on urgency
    response_times = {
        "EMERGENCY": "immediately",
        "HIGH": "within 4 hours",
        "MEDIUM": "within 24 hours",
        "LOW": "within 48 hours"
    }
    
    expected_time = response_times.get(urgency, "within 24 hours")
    
    # Truncate issue if too long
    issue_display = issue_raw[:50] + "..." if len(issue_raw) > 50 else issue_raw
    
    # Format message
    message = f"""Thanks for your maintenance request!

We've created ticket #{ticket_id[:8]} for "{issue_display}" at Unit {unit_number or 'N/A'}.

Based on urgency ({urgency}), we'll respond {expected_time}.

Reply with any updates or questions."""
    
    try:
        from twilio.rest import Client as TwilioClient
        
        # Note: Twilio client is synchronous, so we run it in a thread
        import asyncio
        loop = asyncio.get_event_loop()
        
        def send_twilio_sms():
            twilio_client = TwilioClient(account_sid, auth_token)
            message_obj = twilio_client.messages.create(
                body=message,
                from_=from_number,
                to=tenant_phone
            )
            return message_obj.sid
        
        # Run in executor to avoid blocking
        message_sid = await loop.run_in_executor(None, send_twilio_sms)
        
        logger.info(f"SMS confirmation sent to {tenant_phone} for ticket {ticket_id}")
        return True
        
    except ImportError:
        logger.error("Twilio SDK not installed. Install with: pip install twilio")
        return False
    except Exception as e:
        logger.error(f"Error sending SMS response: {e}")
        return False


# ============================================================================
# COMBINED NOTIFICATION FUNCTION
# ============================================================================

async def send_ticket_notifications(
    ticket_id: str,
    unit_number: str,
    issue_raw: str,
    urgency: str,
    trade_type: str,
    tenant_phone: Optional[str] = None,
    pm_chat_id: Optional[str] = None,
) -> Dict[str, bool]:
    """
    Send all notifications for a new ticket.
    
    Args:
        ticket_id: The ID of the created ticket
        unit_number: Unit number where issue occurred
        issue_raw: Raw description of the issue
        urgency: Urgency level
        trade_type: Classified trade type
        tenant_phone: Tenant's phone number (optional)
        pm_chat_id: Property manager's Telegram chat ID (optional)
    
    Returns:
        Dictionary with notification results: {"telegram": bool, "sms": bool}
    """
    results = {
        "telegram": False,
        "sms": False
    }
    
    # Send Telegram alert to property manager
    if unit_number or issue_raw:
        results["telegram"] = await send_telegram_alert(
            ticket_id=ticket_id,
            unit_number=unit_number,
            issue_raw=issue_raw,
            urgency=urgency,
            trade_type=trade_type,
            pm_chat_id=pm_chat_id
        )
    
    # Send SMS confirmation to tenant
    if tenant_phone:
        results["sms"] = await send_sms_response(
            tenant_phone=tenant_phone,
            ticket_id=ticket_id,
            unit_number=unit_number,
            issue_raw=issue_raw,
            urgency=urgency
        )
    
    return results
