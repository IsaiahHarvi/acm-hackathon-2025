#!/usr/bin/env python3
import os
from math import atan2, cos, radians, sin, sqrt

import nexradaws
import pandas as pd
import pyart
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

CACHE_DIR = os.path.join(os.getcwd(), "nexrad_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points (in km) using the Haversine formula."""
    R = 6371.0  # Earth's radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def get_nearby_radars(target_lat, target_lon, radius_km=100):
    station_df = pd.read_csv("data/nexrad_stations.csv")
    station_df["distance_km"] = station_df.apply(
        lambda row: haversine_distance(
            target_lat, target_lon, row["Latitude"], row["Longitude"]
        ),
        axis=1,
    )
    return station_df[station_df["distance_km"] <= radius_km].sort_values("distance_km")


def get_scan_metadata(filename):
    """
    Open the radar scan file using Py-ART and extract metadata.
    Assumes the file is a NEXRAD level II archive.

    Returns a dict with:
      - filename
      - scan_time (ISO string)
      - rows, cols: dimensions of the reflectivity grid
      - min_lon, max_lon, min_lat, max_lat: geographic bounds from sweep 0.
    """
    file_path = os.path.join(CACHE_DIR, filename)
    try:
        radar = pyart.io.read_nexrad_archive(file_path)
    except Exception as e:
        return {"error": f"Failed to read radar file: {e}"}

    try:
        scan_time = pd.to_datetime(filename[4:17], format="%Y%m%d_%H%M").tz_localize(
            "UTC"
        )
    except Exception as _:
        scan_time = None

    if "reflectivity" not in radar.fields:
        return {"error": "No reflectivity field found in scan."}

    reflectivity_data = radar.fields["reflectivity"]["data"]
    rows, cols = reflectivity_data.shape

    try:
        lats, lons, _ = radar.get_gate_lat_lon_alt(
            sweep=0
        )  # NOTE: this is just for sweep 0
        lats_sweep = lats[0]
        lons_sweep = lons[0]
        min_lon_val = float(lons_sweep.min())
        max_lon_val = float(lons_sweep.max())
        min_lat_val = float(lats_sweep.min())
        max_lat_val = float(lats_sweep.max())
    except Exception as e:
        return {"error": f"Failed to compute bounds: {e}"}

    return {
        "filename": filename,
        "scan_time": scan_time.isoformat() if scan_time else None,
        "rows": rows,
        "cols": cols,
        "min_lon": min_lon_val,
        "max_lon": max_lon_val,
        "min_lat": min_lat_val,
        "max_lat": max_lat_val,
    }


@app.route("/")
def index():
    """
    Landing page that lists all available routes.
    """
    routes = []
    for rule in app.url_map.iter_rules():
        # Skip static routes
        if rule.endpoint == "static":
            continue

        methods = ", ".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
        url = str(rule)
        doc = app.view_functions[rule.endpoint].__doc__
        routes.append(
            f"<li><strong>{methods}</strong> <code>{url}</code><br>{doc or ''}</li>"
        )

    html = f"""
    <html>
    <head>
        <title>NEXRAD API Index</title>
        <style>
            body {{ font-family: sans-serif; padding: 2rem; }}
            code {{ background: #f4f4f4; padding: 0.2em 0.4em; border-radius: 3px; }}
            li {{ margin-bottom: 1em; }}
        </style>
    </head>
    <body>
        <h1>🌩️ NEXRAD Radar Flask API</h1>
        <p>Available endpoints:</p>
        <ul>
            {"".join(routes)}
        </ul>
    </body>
    </html>
    """
    return html


@app.route("/api/scans", methods=["GET"])
def list_scans():
    """
    List relevant available radar scan files
    """
    try:
        files = [
            f
            for f in os.listdir(CACHE_DIR)
            if os.path.isfile(os.path.join(CACHE_DIR, f)) and not f.endswith("MDM")
        ]
        return jsonify({"scans": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scans/<path:filename>", methods=["GET"])
def get_scan(filename):
    """
    Serve a specific radar scan file from the cache directory.
    """
    try:
        return send_from_directory(CACHE_DIR, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@app.route("/api/metadata/<path:filename>", methods=["GET"])
def get_metadata(filename):
    """
    Retrieve metadata for a specific radar scan file.
    """
    meta = get_scan_metadata(filename)
    if "error" in meta:
        return jsonify(meta), 500
    return jsonify(meta)


@app.route("/api/download_scans", methods=["POST"])
def download_scans_endpoint():
    """
    Trigger a download of new radar scans.

    Expected JSON payload:
      {
         "radar_id": "KDVN",
         "start": "2020-08-10T16:30:00Z", // example
         "end": "2020-08-10T21:00:00Z"    //
      }

    This endpoint downloads available scans into the CACHE_DIR and returns
    a list of downloaded filenames.
    """
    data = request.get_json()
    radar_id = data.get("radar_id", "KDVN")
    try:
        start = pd.to_datetime(data["start"]).tz_convert("UTC")
        end = pd.to_datetime(data["end"]).tz_convert("UTC")
    except Exception as e:
        return jsonify({"error": "Invalid start or end time", "details": str(e)}), 400

    aws = nexradaws.NexradAwsInterface()
    scans = aws.get_avail_scans_in_range(start, end, radar_id)

    if scans is None:
        return jsonify(
            {"error": "No scans available for the given time range and radar ID."}
        ), 404

    results = aws.download(scans, CACHE_DIR, threads=os.cpu_count() // 2)

    downloaded_files = [scan.filename for scan in results.iter_success()]
    return jsonify({"downloaded_files": downloaded_files})


@app.route("/api/get_stations", methods=["POST"])
def get_stations():
    """
    Return all nearby radar stations

    Expects:
    target_lat, target_lon, and radius_km
    """
    data = request.get_json()
    target_lat = data.get("target_lat")
    target_lon = data.get("target_lon")
    radius_km = data.get("radius_km", 200)

    return jsonify(
        {
            "radars": get_nearby_radars(target_lat, target_lon, radius_km)[
                ["Radar ID", "Site Name", "distance_km"]
            ]
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5171)
