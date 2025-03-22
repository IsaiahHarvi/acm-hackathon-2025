<script lang="ts">
	import '../app.css';
	let { children } = $props();
</script>

<div class="w-screen h-screen overflow-hidden flex items-center justify-center bg-black">
    {@render children?.()}
</div>