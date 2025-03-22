<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import maplibregl from 'maplibre-gl';
    import 'maplibre-gl/dist/maplibre-gl.css';
    import { current_lat_long } from '$lib/stores/current_location';

    let map;
    let mapElement;
    let initialView = { lat: 39.8283, long: -98.5795 };
    const MAPTILER_API_KEY = 'rIQyeDoL1FNvjM5uLY2f';

    onMount(() => {
        if (typeof window !== 'undefined') {
            navigator.geolocation.getCurrentPosition((position) => {
                current_lat_long.set({
                    lat: position.coords.latitude,
                    long: position.coords.longitude
                });
            });
        }

        if ($current_lat_long.lat && $current_lat_long.long) {
            initialView = $current_lat_long;
        }
        
        map = new maplibregl.Map({
            container: mapElement,
            style: `https://api.maptiler.com/maps/streets/style.json?key=${MAPTILER_API_KEY}`,
            center: [initialView.long, initialView.lat],
            zoom: 17
        });
    });

    onDestroy(() => {
        if (map) {
            console.log('Unloading MapTiler map.');
            map.remove();
        }
    });
</script>

<div class="h-screen w-screen" bind:this={mapElement}></div>
