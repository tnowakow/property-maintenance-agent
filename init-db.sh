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

# Use PUBLIC URL for local execution, internal URL works inside Railway
# When running locally with 'railway run', use DATABASE_PUBLIC_URL
# When running inside a deployed service, DATABASE_URL works fine
if [ -n "$DATABASE_PUBLIC_URL" ]; then
    echo "Using public database URL (for local execution)"
    DB_CONNECTION="$DATABASE_PUBLIC_URL"
else
    echo "Using internal database URL (inside Railway network)"
    DB_CONNECTION="$DATABASE_URL"
fi
echo ""

echo "Creating database schema..."
psql "$DB_CONNECTION" -f postgres-schema.sql

if [ $? -eq 0 ]; then
    echo "✓ Schema created successfully"
else
    echo "ERROR: Failed to create schema"
    exit 1
fi

echo ""
echo "Seeding demo data..."
psql "$DB_CONNECTION" -f seed-data.sql

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
psql "$DB_CONNECTION" -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"

echo ""
echo "Record counts:"
psql "$DB_CONNECTION" -c "SELECT 'properties' as table_name, COUNT(*) as count FROM properties UNION ALL SELECT 'units', COUNT(*) FROM units UNION ALL SELECT 'vendors', COUNT(*) FROM vendors UNION ALL SELECT 'tickets', COUNT(*) FROM tickets;"
