#!/usr/bin/env python3
import json

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np

from services.collector.utils import get_postgres_connection


def query_scans():
    """
    Query the radar_scans table for all stored scans.
    """
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT radar_id, scan_time, grid_data, min_lon, max_lon, min_lat, max_lat
        FROM radar_scans
        ORDER BY scan_time;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def plot_scan_from_db(scan):
    radar_id, scan_time, grid_data_json, min_lon, max_lon, min_lat, max_lat = scan
    grid_data = json.loads(grid_data_json)
    reflectivity = grid_data.get("reflectivity", [])
    refl_array = np.array(reflectivity)
    if refl_array.ndim == 1:
        refl_array = refl_array.reshape(1, -1)

    projection = ccrs.PlateCarree()
    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={"projection": projection})
    ax.set_extent([min_lon, max_lon, min_lat, max_lat])

    im = ax.imshow(
        refl_array,
        origin="upper",
        extent=[min_lon, max_lon, min_lat, max_lat],
        cmap="HomeyerRainbow",
        vmin=-7.5,
        vmax=65,
        transform=ccrs.PlateCarree(),
    )
    plt.colorbar(im, ax=ax, orientation="horizontal", pad=0.05)
    ax.set_title(f"Radar {radar_id} Reflectivity at {scan_time}")
    plt.show()


def main():
    scans = query_scans()
    if not scans:
        print("No scans found in the database.")
        return
    first_scan = scans[0]
    plot_scan_from_db(first_scan)


if __name__ == "__main__":
    main()
