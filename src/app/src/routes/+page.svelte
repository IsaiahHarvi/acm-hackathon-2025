<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import maplibregl from 'maplibre-gl';
    import 'maplibre-gl/dist/maplibre-gl.css';
    import { current_lat_long } from '$lib/stores/current_location';

    let map;
    let mapElement;
    let initialView = { lat: 39.8283, long: -98.5795 };
    const MAPTILER_API_KEY = 'rIQyeDoL1FNvjM5uLY2f';

    // RainViewer settings
    let radarLayers = [];
    let animationPosition = 0;
    let animationTimer = null;
    const FRAME_COUNT = 1;
    const FRAME_DELAY = 1500; // milliseconds between frames
    const RESTART_DELAY = 1000; // milliseconds before restarting animation
    const COLOR_SCHEME = 7; // 1: Original, 2: Universal Blue, 3: TITAN, etc.

    // Create play/pause button
    let playButton;
    let isPlaying = true;

    function togglePlayPause() {
        isPlaying = !isPlaying;
        if (isPlaying) {
            animationTimer = setInterval(nextFrame, FRAME_DELAY);
        } else {
            clearInterval(animationTimer);
        }
    }

    function nextFrame() {
        if (!radarLayers.length) return;
        
        // Hide the current layer
        if (radarLayers[animationPosition]) {
            map.setLayoutProperty(
                radarLayers[animationPosition].id,
                'visibility',
                'none'
            );
        }

        // Move to the next frame
        animationPosition = (animationPosition + 1) % radarLayers.length;
        
        // Show the next layer
        if (radarLayers[animationPosition]) {
            map.setLayoutProperty(
                radarLayers[animationPosition].id,
                'visibility',
                'visible'
            );
            
            // Update timestamp display if we have a timestamp element
            const timestamp = document.getElementById('radar-timestamp');
            if (timestamp && radarLayers[animationPosition].time) {
                timestamp.textContent = formatTimestamp(radarLayers[animationPosition].time * 1000);
            }
            
            // Update progress bar
            const progressBar = document.getElementById('progress-bar');
            if (progressBar) {
                progressBar.style.width = `${((animationPosition + 1) / radarLayers.length) * 100}%`;
            }
        }
        
        // If we're at the end, wait a bit longer before restarting
        if (animationPosition === radarLayers.length - 1) {
            clearInterval(animationTimer);
            setTimeout(() => {
                if (isPlaying) {
                    animationTimer = setInterval(nextFrame, FRAME_DELAY);
                }
            }, RESTART_DELAY - FRAME_DELAY);
        }
    }
    
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const weekday = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        
        return `${weekday[date.getDay()]} ${month[date.getMonth()]} ${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    }

    function loadRainViewerData() {
        return fetch('https://api.rainviewer.com/public/weather-maps.json')
            .then(res => res.json())
            .then(data => {
                // Clear any existing radar layers
                if (radarLayers.length) {
                    radarLayers.forEach(layer => {
                        if (map.getLayer(layer.id)) {
                            map.removeLayer(layer.id);
                        }
                        if (map.getSource(layer.id)) {
                            map.removeSource(layer.id);
                        }
                    });
                    radarLayers = [];
                }
                
                // Get the radar data - most recent frames
                const radarFrames = data.radar.past.slice(-FRAME_COUNT);
                
                // Add each frame as a separate layer
                radarFrames.forEach((frame, index) => {
                    const layerId = `radar-layer-${index}`;
                    const frameTime = frame.time;
                    
                    // Add the source
                    map.addSource(layerId, {
                        type: 'raster',
                        tiles: [
                            `https://tilecache.rainviewer.com/v2/radar/${frameTime}/256/{z}/{x}/{y}/${COLOR_SCHEME}/1_0.png`
                        ],
                        tileSize: 256
                    });
                    
                    // Add the layer
                    map.addLayer({
                        id: layerId,
                        type: 'raster',
                        source: layerId,
                        layout: {
                            visibility: index === 0 ? 'visible' : 'none'
                        },
                        paint: {
                            'raster-opacity': 0.8
                        }
                    });
                    
                    // Store the layer info
                    radarLayers.push({
                        id: layerId,
                        time: frameTime
                    });
                });
                
                // Set initial position
                animationPosition = 0;
                
                // Update timestamp if we have a timestamp element
                const timestamp = document.getElementById('radar-timestamp');
                if (timestamp && radarLayers[0] && radarLayers[0].time) {
                    timestamp.textContent = formatTimestamp(radarLayers[0].time * 1000);
                }
                
                // Start the animation
                if (isPlaying) {
                    clearInterval(animationTimer);
                    animationTimer = setInterval(nextFrame, FRAME_DELAY);
                }
                
                // Schedule the next update (every 5 minutes)
                setTimeout(loadRainViewerData, 5 * 60 * 1000);
            })
            .catch(err => {
                console.error('Error loading RainViewer data:', err);
                // Try again in 30 seconds
                setTimeout(loadRainViewerData, 30 * 1000);
            });
    }

    onMount(() => {
        if (typeof window !== 'undefined') {
            navigator.geolocation.getCurrentPosition((position) => {
                current_lat_long.set({
                    lat: position.coords.latitude,
                    long: position.coords.longitude
                });
                
                // If the map is already loaded, fly to this position
                if (map) {
                    map.flyTo({
                        center: [position.coords.longitude, position.coords.latitude],
                        zoom: 8,
                        essential: true
                    });
                }
            });
        }

        if ($current_lat_long.lat && $current_lat_long.long) {
            initialView = $current_lat_long;
        }

        map = new maplibregl.Map({
            container: mapElement,
            style: `https://api.maptiler.com/maps/darkmatter/style.json?key=${MAPTILER_API_KEY}`,
            center: [initialView.long, initialView.lat],
            zoom: 8
        });
        
        map.on('load', () => {
            // Add home marker
            map.loadImage('/marker-icon.png', (error, image) => {
                if (error) throw error;
                
                map.addImage('home-marker', image);
                
                map.addSource('home', {
                    type: 'geojson',
                    data: {
                        type: 'FeatureCollection',
                        features: [{
                            type: 'Feature',
                            geometry: {
                                type: 'Point',
                                coordinates: [initialView.long, initialView.lat]
                            }
                        }]
                    }
                });
                
                map.addLayer({
                    id: 'home-marker',
                    type: 'symbol',
                    source: 'home',
                    layout: {
                        'icon-image': 'home-marker',
                        'icon-size': 0.5
                    }
                });
            });
            
            // Add radar layers
            loadRainViewerData();
            
            // Create controls container if it doesn't exist
            if (!document.getElementById('map-controls')) {
                const controlsContainer = document.createElement('div');
                controlsContainer.id = 'map-controls';
                controlsContainer.className = 'map-control-container';
                
                // Create play/pause button
                playButton = document.createElement('button');
                playButton.className = 'map-control-button';
                playButton.innerHTML = isPlaying ? '⏸️' : '▶️';
                playButton.onclick = () => {
                    togglePlayPause();
                    playButton.innerHTML = isPlaying ? '⏸️' : '▶️';
                };
                
                controlsContainer.appendChild(playButton);
                
                // Add controls to the map
                document.querySelector('.maplibregl-ctrl-bottom-right').appendChild(controlsContainer);
            }
        });
    });

    onDestroy(() => {
        if (map) {
            console.log('Unloading MapTiler map.');
            if (animationTimer) {
                clearInterval(animationTimer);
            }
            map.remove();
        }
    });
</script>

<div class="relative h-screen w-screen">
    <div class="absolute top-0 left-0 w-full h-8 bg-gray-800 z-10 flex items-center px-2 text-white justify-between">
        <div id="radar-timestamp" class="text-sm"></div>
        <div class="text-xs">Radar data by <a href="https://rainviewer.com" class="text-blue-300 hover:text-blue-200" target="_blank">RainViewer</a></div>
    </div>
    
    <div class="absolute bottom-0 left-0 w-full h-1 bg-gray-800 z-10">
        <div id="progress-bar" class="h-full bg-blue-500" style="width: 0%"></div>
    </div>
    
    <div class="absolute top-8 left-0 w-full z-10 flex justify-center">
        <div class="radar-color-scale bg-white px-2 py-1 rounded shadow-md flex items-center text-xs">
            <span>Light</span>
            <div class="mx-1 w-64 h-4 bg-gradient-to-r from-blue-300 via-yellow-300 to-red-500"></div>
            <span>Heavy</span>
        </div>
    </div>
    
    <div class="h-full w-full" bind:this={mapElement}></div>
</div>

<style>
    .map-control-container {
        background: white;
        border-radius: 4px;
        padding: 5px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        margin: 10px;
    }
    
    .map-control-button {
        width: 30px;
        height: 30px;
        border: none;
        background: white;
        cursor: pointer;
        border-radius: 4px;
    }
    
    .map-control-button:hover {
        background: #f0f0f0;
    }
</style>