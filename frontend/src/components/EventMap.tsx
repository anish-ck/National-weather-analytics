import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { ScatterplotLayer } from '@deck.gl/layers';
import { HeatmapLayer } from '@deck.gl/aggregation-layers';
import type { WeatherEvent } from '../types';

const colour: Record<string, [number, number, number]> = { SUPPORTED:[34,197,94], REFUTED:[239,68,68], MISLEADING:[249,115,22], UNCERTAIN:[148,163,184] };
export function EventMap({ events, onSelect }: { events: WeatherEvent[]; onSelect:(event:WeatherEvent)=>void }) {
 const element = useRef<HTMLDivElement>(null); const map = useRef<maplibregl.Map | null>(null); const overlay = useRef<MapboxOverlay | null>(null);
 useEffect(() => { if (!element.current || map.current) return; map.current = new maplibregl.Map({ container:element.current, style:'https://demotiles.maplibre.org/style.json', center:[78.96,22.59], zoom:3.5, attributionControl:false }); overlay.current = new MapboxOverlay({ interleaved:true, layers:[] }); map.current.addControl(overlay.current); return () => map.current?.remove(); }, []);
 useEffect(() => { const points = events.filter(e => e.latitude != null && e.longitude != null); overlay.current?.setProps({ layers:[new HeatmapLayer({ id:'event-heat', data:points, getPosition:(e:WeatherEvent)=>[e.longitude!,e.latitude!], getWeight:(e:WeatherEvent)=>e.confidence_score, radiusPixels:42 }), new ScatterplotLayer({ id:'event-points', data:points, pickable:true, getPosition:(e:WeatherEvent)=>[e.longitude!,e.latitude!], getFillColor:(e:WeatherEvent)=>colour[e.verification_status], getRadius:85000, radiusMinPixels:7, radiusMaxPixels:20, onClick:({object})=>object && onSelect(object as WeatherEvent) })] }); }, [events, onSelect]);
 return <div className="map" ref={element}><div className="map-label">LIVE EVENT DENSITY</div></div>;
}
