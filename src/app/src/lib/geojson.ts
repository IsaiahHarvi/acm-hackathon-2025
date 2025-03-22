export async function get_pieces() {
	const metadataResponse = await fetch('/api/radar?metadata=true');
	if (!metadataResponse.ok) {
		throw new Error(`Failed to fetch radar metadata: ${metadataResponse.statusText}`);
	}

	const radarMetadata = await metadataResponse.json();

	const res = await fetch('/api/radar', {
		method: 'GET'
	});

	const radarResponse = await res.json();

	const blob = await radarResponse.blob();
	const radarImageUrl = URL.createObjectURL(blob);

	return radarMetadata;
}
