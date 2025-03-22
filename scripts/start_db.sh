#!/usr/bin/env bash

docker compose down -v || true
docker compose up
docker exec -it postgres psql -U admin -d weather_db -c "CREATE TABLE IF NOT EXISTS radar_scans (id SERIAL PRIMARY KEY, radar_id TEXT, scan_time TIMESTAMPTZ, grid_data JSONB, min_lon NUMERIC, max_lon NUMERIC, min_lat NUMERIC, max_lat NUMERIC);"
