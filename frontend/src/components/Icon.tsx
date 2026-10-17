const paths = {
 book: "M4 4h6a3 3 0 0 1 2 3v14a4 4 0 0 0-4-3H4z M20 4h-6a3 3 0 0 0-2 3v14a4 4 0 0 1 4-3h4z",
 grid: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
 list: "M8 6h13 M8 12h13 M8 18h13 M3 6h.01 M3 12h.01 M3 18h.01",
 plus: "M12 5v14 M5 12h14", arrow: "M5 12h14 M13 6l6 6-6 6",
 search: "M21 21l-5-5 M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0",
 check: "M5 12l4 4L19 6", spark: "M12 3l2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z",
 shield: "M12 3l8 3v6c0 5-8 9-8 9s-8-4-8-9V6z M8 12l3 3 5-6",
 clock: "M12 8v5l3 2 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0",
 logout: "M9 4H4v16h5 M10 12h11 M16 7l5 5-5 5",
} as const;
export default function Icon({ name, size = 20 }: { name: keyof typeof paths; size?: number }) {
 return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>;
}
