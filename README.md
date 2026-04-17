# Property Maintenance Agent - FastAPI Backend

This is the FastAPI backend for the Property Maintenance Agent system that handles tenant maintenance requests from intake to dispatch with zero human intervention.

## Features

- **Intake Endpoints**: Handle SMS, voice calls, and web form submissions
- **Ticket Management**: Create, retrieve, and update tickets in Supabase
- **Agent Integration**: Trigger OpenClaw triage processing
- **Health Checks**: Monitor API status
- **Error Handling**: Comprehensive error handling and logging

## Endpoints

### Intake Endpoints
- `POST /intake/sms` - Handle Twilio SMS webhook
- `POST /intake/voice` - Handle Twilio voice transcript webhook
- `POST /intake/web` - Handle web form submissions

### Ticket Management
- `GET /ticket/{id}` - Retrieve ticket by ID
- `POST /agent/process` - Trigger OpenClaw agent processing

### Health Check
- `GET /health` - Health check endpoint

## Environment Variables

Copy `.env.example` to `.env` and set the required values:

```
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key-here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENCLAW_API_URL=http://localhost:8080/api
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file

3. Run the application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Database Schema

The backend interacts with Supabase tables:
- `tickets` - Stores maintenance requests
- `units` - Stores property units
- `properties` - Stores property information
- `vendors` - Stores vendor information

## Error Handling

All endpoints include proper error handling with logging for debugging and monitoring.