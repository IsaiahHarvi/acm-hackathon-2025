<script lang="ts">
	import '../app.css';
	let { children } = $props();
</script>

<div class="w-screen h-screen flex items-center justify-centern bg-black">
    {@render children()}
</div>