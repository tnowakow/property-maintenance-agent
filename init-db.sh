#!/bin/bash
# Property Maintenance Agent - Database Initialization Script
# Run this on Railway to set up the PostgreSQL database

set -e  # Exit on error

echo "=========================================="
echo "Database Initialization Script"
echo "=========================================="
echo ""

# Check if DATABASE_URL is set (Railway provides this automatically)
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable not set!"
    echo "This should be provided automatically by Railway PostgreSQL plugin."
    exit 1
fi

echo "✓ DATABASE_URL is configured"
echo "DATABASE_URL (first 50 chars): ${DATABASE_URL:0:50}..."
echo ""

# Convert DATABASE_URL to psql-compatible format
# Railway provides: postgresql://user:password@host:port/dbname
# psql needs: host, user, password, dbname separately or use PGPASSWORD

echo "Creating database schema..."
psql "$DATABASE_URL" -f /app/postgres-schema.sql

if [ $? -eq 0 ]; then
    echo "✓ Schema created successfully"
else
    echo "ERROR: Failed to create schema"
    exit 1
fi

echo ""
echo "Seeding demo data..."
psql "$DATABASE_URL" -f /app/seed-data.sql

if [ $? -eq 0 ]; then
    echo "✓ Demo data seeded successfully"
else
    echo "WARNING: Failed to seed demo data (tables may already exist)"
fi

echo ""
echo "=========================================="
echo "Database initialization complete!"
echo "=========================================="
echo ""

# Verify tables were created
echo "Verifying database setup..."
psql "$DATABASE_URL" -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"

echo ""
echo "Record counts:"
psql "$DATABASE_URL" -c "SELECT 'properties' as table_name, COUNT(*) as count FROM properties UNION ALL SELECT 'units', COUNT(*) FROM units UNION ALL SELECT 'vendors', COUNT(*) FROM vendors UNION ALL SELECT 'tickets', COUNT(*) FROM tickets;"
