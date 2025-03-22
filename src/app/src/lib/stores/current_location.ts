import { persisted } from 'svelte-persisted-store';

export const current_lat_long = persisted('current_lat_long', {
	lat: 36.1627,
	long: -86.7816
});
