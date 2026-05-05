# Property Maintenance Dashboard - Combined Backend + Frontend
FROM python:3.11-slim

# Install Node.js for building frontend
RUN apt-get update && apt-get install -y \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend code and build it
COPY ../dashboard-v2 ./frontend
WORKDIR /app/frontend
RUN npm ci && npm run build
WORKDIR /app

# Copy backend code
COPY main.py .
COPY database.py .
COPY models.py .
COPY utils.py .
COPY notifications.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
