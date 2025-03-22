#!/usr/bin/env python3
"""
Download NEXRAD scans from AWS for a given radar and time window,
plot reflectivity with severe weather reports, and store the radar
data into a PostgreSQL database for later use by a JavaScript app.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import nexradaws
import numpy as np
import pandas as pd
import psycopg2
import pyart
import pytz
from metpy.plots import USCOUNTIES


# ----------------------------
# Helper: Postgres connection
# ----------------------------
def get_postgres_connection():
    """
    Connect to PostgreSQL using environment variables or defaults.
    Set PG_HOST, PG_DATABASE, PG_USER, PG_PASSWORD in your environment.
    """
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        database=os.getenv("PG_DATABASE", "radardb"),
        user=os.getenv("PG_USER", "user"),
        password=os.getenv("PG_PASSWORD", "password"),
    )
    return conn


# ----------------------------------
# Download, severe reports functions
# ----------------------------------
def download_scans(radar_id, start, end, temp_dir):
    """Download available scans for a given radar in a time window."""
    conn = nexradaws.NexradAwsInterface()
    scans = conn.get_avail_scans_in_range(start, end, radar_id)
    print(f"There are {len(scans)} scans available between {start} and {end}\n")
    print(scans[0:4])
    results = conn.download(scans, temp_dir)
    return results


def load_and_convert(url, start, end):
    """
    Load an SPC CSV file, localize its datetime (assumed to be in CST, UTC+6),
    sort the index, and subset to 30 minutes before start and 30 minutes after end.
    """
    df = pd.read_csv(url)
    df["datetime"] = pd.to_datetime(df.date + " " + df.time)
    df.set_index("datetime", inplace=True)
    df.index = df.index.tz_localize(
        "Etc/GMT+6", ambiguous="NaT", nonexistent="shift_forward"
    ).tz_convert("UTC")
    df.sort_index(inplace=True)
    start_str = (start - pd.Timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M")
    end_str = (end + pd.Timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M")
    return df[start_str:end_str]


def load_severe_reports(year, start, end):
    """Download and process SPC severe weather reports for wind, tornado, and hail."""
    year_str = str(year)
    wind_url = f"https://www.spc.noaa.gov/wcm/data/{year_str}_wind.csv"
    torn_url = f"https://www.spc.noaa.gov/wcm/data/{year_str}_torn.csv"
    hail_url = f"https://www.spc.noaa.gov/wcm/data/{year_str}_hail.csv"

    wind_rpts = load_and_convert(wind_url, start, end)
    tor_rpts = load_and_convert(torn_url, start, end)
    hail_rpts = load_and_convert(hail_url, start, end)
    return wind_rpts, tor_rpts, hail_rpts


# -----------------------
# Plotting Functionality
# -----------------------
def plot_scan(
    scan,
    radar_id,
    start,
    min_lon,
    max_lon,
    min_lat,
    max_lat,
    wind_rpts,
    tor_rpts,
    hail_rpts,
):
    """
    Plot a single radar scan (if not an MDM file) with reflectivity data
    and overlay severe weather reports.
    """
    if scan.filename[-3:] == "MDM":
        return

    print(f"Processing scan: {scan.filename}")
    # Extract scan time from the filename; adjust format if needed.
    this_time = pd.to_datetime(scan.filename[4:17], format="%Y%m%d_%H%M").tz_localize(
        "UTC"
    )
    radar = scan.open_pyart()

    # Set up figure and map projection
    fig = plt.figure(figsize=(15, 7))
    projection = ccrs.PlateCarree()
    ax = fig.add_axes([0.05, 0.05, 0.4, 0.80], projection=projection)

    # Add geographic features
    ax.add_feature(USCOUNTIES.with_scale("500k"), edgecolor="gray", linewidth=0.4)
    ax.add_feature(cfeature.STATES.with_scale("10m"), linewidth=1.0)

    # Create a gate filter to mask reflectivity values below -2.5 dBZ
    gatefilter = pyart.filters.GateFilter(radar)
    gatefilter.exclude_below("reflectivity", -2.5)

    display = pyart.graph.RadarMapDisplay(radar)
    title_str = f"{radar_id} Reflectivity and Severe Weather Reports\n{this_time.strftime('%H%M UTC %d %b %Y')}"
    # Use the valid Py-ART colormap "HomeyerRainbow"
    cf = display.plot_ppi_map(
        "reflectivity",
        0,
        vmin=-7.5,
        vmax=65,
        min_lon=min_lon,
        max_lon=max_lon,
        min_lat=min_lat,
        max_lat=max_lat,
        title=title_str,
        projection=projection,
        resolution="10m",
        gatefilter=gatefilter,
        cmap="HomeyerRainbow",
        colorbar_flag=False,
        lat_lines=[0, 0],
        lon_lines=[0, 0],
    )
    display.plot_colorbar(cf, orient="horizontal", pad=0.07)
    ax.set_xticks(np.arange(min_lon, max_lon, 0.5), crs=ccrs.PlateCarree())
    ax.set_yticks(np.arange(min_lat, max_lat, 0.5), crs=ccrs.PlateCarree())

    # Subset severe reports from 30 minutes before start up to the scan time
    time_str = this_time.strftime("%Y-%m-%d %H:%M")
    start_window = (start - pd.Timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M")
    wind_now = wind_rpts[start_window:time_str]
    tor_now = tor_rpts[start_window:time_str]
    hail_now = hail_rpts[start_window:time_str]

    # Overlay severe weather reports (scatter markers)
    ax.scatter(
        wind_now.slon.values,
        wind_now.slat.values,
        s=20,
        facecolors="none",
        edgecolors="mediumblue",
        linewidths=1.8,
        transform=ccrs.PlateCarree(),
    )
    ax.scatter(
        tor_now.slon.values,
        tor_now.slat.values,
        s=20,
        facecolors="red",
        edgecolors="black",
        marker="v",
        linewidths=1.5,
        transform=ccrs.PlateCarree(),
    )
    ax.scatter(
        hail_now.slon.values,
        hail_now.slat.values,
        s=20,
        facecolors="none",
        edgecolors="green",
        linewidths=1.8,
        transform=ccrs.PlateCarree(),
    )

    # Save the plot as a PNG file
    output_filename = f"{radar_id}_{scan.filename[4:17]}_reflectivity_reports.png"
    plt.savefig(
        output_filename,
        bbox_inches="tight",
        dpi=300,
        facecolor="white",
        transparent=False,
    )
    print(f"Saved plot as {output_filename}")
    plt.close(fig)


# -------------------------------
# Function to Store Scan in Postgres
# -------------------------------
def store_scan_in_postgres(scan, radar, radar_id):
    """
    Extract the reflectivity data from sweep 0 along with the spatial bounds,
    then store these values in a PostgreSQL table (using a JSONB field for grid_data).
    """
    # Extract scan time from filename
    scan_time = pd.to_datetime(scan.filename[4:17], format="%Y%m%d_%H%M").tz_localize(
        "UTC"
    )

    # Extract reflectivity for sweep 0 and convert to list
    reflectivity_data = radar.fields["reflectivity"]["data"][0]
    reflectivity_list = reflectivity_data.tolist()

    # Get gate latitude and longitude for sweep 0 and compute bounds
    lats = radar.gate_latitude[0]
    lons = radar.gate_longitude[0]
    min_lon_val = float(lons.min())
    max_lon_val = float(lons.max())
    min_lat_val = float(lats.min())
    max_lat_val = float(lats.max())

    # Create a dictionary to hold grid data
    grid_data = {
        "reflectivity": reflectivity_list,
        "min_lon": min_lon_val,
        "max_lon": max_lon_val,
        "min_lat": min_lat_val,
        "max_lat": max_lat_val,
    }

    # Connect to Postgres and insert the record
    conn = get_postgres_connection()
    cur = conn.cursor()
    insert_sql = """
    INSERT INTO radar_scans (radar_id, scan_time, grid_data, min_lon, max_lon, min_lat, max_lat)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cur.execute(
        insert_sql,
        (
            radar_id,
            scan_time,
            json.dumps(grid_data),
            min_lon_val,
            max_lon_val,
            min_lat_val,
            max_lat_val,
        ),
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"Stored scan {scan.filename} in Postgres.")


# ---------------------
# Main processing loop
# ---------------------
def main():
    # ---------------------
    # Configuration
    # ---------------------
    radar_id = "KDVN"
    # Define time window (example: Aug 10, 2020)
    start = pd.Timestamp(2020, 8, 10, 16, 30).tz_localize("UTC")
    end = pd.Timestamp(2020, 8, 10, 21, 0).tz_localize("UTC")
    # Define map bounds (longitude and latitude)
    min_lon, max_lon = -93.25, -88.0
    min_lat, max_lat = 40.35, 43.35

    # Create a temporary directory for downloaded scans
    temp_location = tempfile.mkdtemp()
    print(f"Using temporary directory: {temp_location}")

    # Download NEXRAD scans via AWS
    scans = download_scans(radar_id, start, end, temp_location)

    # Load severe weather reports from SPC for the corresponding year
    wind_rpts, tor_rpts, hail_rpts = load_severe_reports(start.year, start, end)

    # Loop over each downloaded scan and process
    for i, scan in enumerate(scans.iter_success(), start=1):
        # Skip files ending with "MDM"
        if scan.filename[-3:] == "MDM":
            continue
        print(f"Processing scan: {scan.filename}")
        radar = scan.open_pyart()
        plot_scan(
            scan,
            radar_id,
            start,
            min_lon,
            max_lon,
            min_lat,
            max_lat,
            wind_rpts,
            tor_rpts,
            hail_rpts,
        )
        store_scan_in_postgres(scan, radar, radar_id)


if __name__ == "__main__":
    main()
