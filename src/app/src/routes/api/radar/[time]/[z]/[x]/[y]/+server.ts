import axios from 'axios';
import { json } from '@sveltejs/kit';

// Helper function to fetch radar tile from RainViewer
async function fetchRadarTile(time: string, z: string, x: string, y: string) {
	const radarUrl = `https://tilecache.rainviewer.com/v2/radar/${time}/256/${z}/${x}/${y}/1/1_0.png`;

	try {
		const response = await axios.get(radarUrl, { responseType: 'arraybuffer' });
		return response.data; // Returning the binary data of the tile
	} catch (error) {
		throw new Error(`Failed to fetch radar tile: ${error.message}`);
	}
}

export async function GET({ params }) {
	const { time, z, x, y } = params;

	try {
		// Fetch the radar tile image data
		const tileData = await fetchRadarTile(time, z, x, y);

		// Return the image data as a PNG
		return new Response(tileData, {
			headers: {
				'Content-Type': 'image/png',
				'Access-Control-Allow-Origin': '*', // Allow cross-origin requests
				'Cache-Control': 'public, max-age=86400' // Cache the tile for 1 day
			}
		});
	} catch (error) {
		console.error('Error fetching radar tile:', error);
		return json(
			{ success: false, error: 'Failed to fetch radar tile', details: error.message },
			{ status: 500 }
		);
	}
}
