#!/usr/bin/env bash

docker compose down -v || true
docker compose up -d

# Wait for a few seconds to let PostgreSQL start
echo "Waiting for PostgreSQL to start..."
sleep 10

docker compose exec postgres psql -U admin -d weather_db -c "CREATE TABLE IF NOT EXISTS radar_scans (id SERIAL PRIMARY KEY, radar_id TEXT, scan_time TIMESTAMPTZ, grid_data JSONB, min_lon NUMERIC, max_lon NUMERIC, min_lat NUMERIC, max_lat NUMERIC);"

docker logs -f postgres
