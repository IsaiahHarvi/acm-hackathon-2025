import { Level2Radar } from 'nexrad-level-2-data';
import { plot, writePngToFile } from 'nexrad-level-2-plot';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { json } from '@sveltejs/kit';

// Get the current file's directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export async function GET({ url }) {
	try {
		const filePath = path.resolve(process.cwd(), 'src/lib/content/nexrad-l2');
		const rawData = await fs.readFile(filePath);
		const radar = new Level2Radar(rawData);

		// Check if metadata is requested
		const metadataOnly = url.searchParams.get('metadata') === 'true';

		if (metadataOnly) {
			// Extract and return metadata from the radar data
			// These fields will depend on what's available in the Level2Radar object
			return json({
				success: true,
				stationId: radar.header.icao,
				stationName: radar.header.icao, // You might need a lookup for the full name
				latitude: radar.header.latitude,
				longitude: radar.header.longitude,
				elevationMeters: radar.header.elevationMeters,
				radar: radar,
				// Calculate bounds based on radar range (typically ~230km for NEXRAD)
				bounds: calculateRadarBounds(
					radar.header.latitude,
					radar.header.longitude,
					230 // radar range in km
				)
			});
		}

		// Generate the plot image
		const plots = await plot(radar, 'REF', { elevations: 1 });
		const plotData = plots[0].REF;

		// Create a PNG stream from the plot data
		const pngStream = plotData.canvas.createPNGStream();

		// Collect the data into a buffer
		const chunks = [];
		for await (const chunk of pngStream) {
			chunks.push(chunk);
		}
		const buffer = Buffer.concat(chunks);

		// Return the image buffer as the response
		return new Response(buffer, {
			headers: {
				'Content-Type': 'image/png',
				'Content-Length': buffer.length
			}
		});
	} catch (error) {
		console.error('Error processing radar data:', error);
		return json(
			{
				success: false,
				error: 'Failed to process radar data',
				details: error.message
			},
			{ status: 500 }
		);
	}
}

// Helper function to calculate radar coverage bounds
function calculateRadarBounds(lat, lon, rangeKm) {
	// Earth radius in kilometers
	const earthRadius = 6371;

	// Convert latitude and longitude to radians
	const latRad = (lat * Math.PI) / 180;
	const lonRad = (lon * Math.PI) / 180;

	// Angular distance in radians
	const angDist = rangeKm / earthRadius;

	// Calculate bounds
	const minLat = lat - rangeKm / 111.32; // approx conversion from km to degrees
	const maxLat = lat + rangeKm / 111.32;

	// Longitude degrees per km varies with latitude
	const lonDegreesPerKm = 111.32 * Math.cos(latRad);
	const lonOffset = rangeKm / lonDegreesPerKm;

	const minLon = lon - lonOffset;
	const maxLon = lon + lonOffset;

	return [
		[minLon, minLat], // Southwest corner [lng, lat]
		[maxLon, maxLat] // Northeast corner [lng, lat]
	];
}
