#!/usr/bin/env python3

import json
import os

import psycopg2
import psycopg2.extras

from services.collector.utils import get_postgres_connection


def fetch_sample_data():
    conn = get_postgres_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = "SELECT * FROM radar_scans LIMIT 1;"
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def main():
    sample_data = fetch_sample_data()
    json_output = json.dumps(sample_data, indent=4, default=str)
    output_file = "sample_data.json"
    with open(output_file, "w") as f:
        f.write(json_output)
    print(f"Sample data written to {output_file}")


if __name__ == "__main__":
    main()
