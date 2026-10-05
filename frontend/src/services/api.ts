import type { Stats, WeatherEvent } from '../types';
const base = import.meta.env.VITE_API_URL ?? '';
export const api = {
 events: (): Promise<WeatherEvent[]> => fetch(`${base}/api/events`).then(r => r.json()),
 stats: (): Promise<Stats> => fetch(`${base}/api/statistics`).then(r => r.json()),
 submit: (data: object) => fetch(`${base}/api/reports`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data) }).then(r => r.json())
};
