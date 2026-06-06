const COLORS = [
	'#3f5bd9',
	'#b94e7e',
	'#3a8f6d',
	'#cfa86d',
	'#6d4ed1',
	'#c2542f',
	'#2f8fc2',
	'#5f5f5f'
];

/** First letter of first + last word, uppercased (or first two letters). */
export function initials(name: string): string {
	const parts = name.trim().split(/\s+/).filter(Boolean);
	if (parts.length === 0) return '?';
	if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
	return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/** Deterministic colour from a name. */
export function monogramColor(name: string): string {
	let hash = 0;
	for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
	return COLORS[hash % COLORS.length];
}
