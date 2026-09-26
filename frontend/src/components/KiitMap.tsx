import { useEffect, useMemo, useRef, useState } from "react";
import L, { divIcon, type LatLngExpression } from "leaflet";
import { Circle, CircleMarker, MapContainer, Marker, Polygon, TileLayer, Tooltip, useMap, useMapEvents } from "react-leaflet";
import { Building2, Check, Expand, LocateFixed, Map, MoonStar, RotateCcw, Search, SunMedium, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { CampusZone, Geofence, GeoPoint, Incident } from "@/lib/types";

interface KiitMapProps {
  zones: CampusZone[];
  incidents: Incident[];
  selectedZoneId: string | null;
  onSelectZone: (zone: CampusZone) => void;
  onSelectIncident: (incident: Incident) => void;
  geofences: Geofence[];
  selectedGeofenceId: string | null;
  draftPoints: GeoPoint[];
  drawing: boolean;
  onAddDraftPoint: (point: GeoPoint) => void;
  onSelectGeofence: (geofence: Geofence) => void;
  onUndoDraft: () => void;
  onCancelDraft: () => void;
  onFinishDraft: () => void;
}

type MapTarget = { center: [number, number]; zoom: number; nonce: number };
type MapStyle = "street" | "light" | "dark";

const CITY: [number, number] = [20.2961, 85.8245];
const KIIT: [number, number] = [20.3548, 85.8192];
const riskColor: Record<CampusZone["risk_level"], string> = { CRITICAL: "#b91c1c", HIGH: "#ea580c", MODERATE: "#d97706", LOW: "#2563eb" };
const severityColor: Record<Incident["severity"], string> = { CRITICAL: "#b91c1c", HIGH: "#ea580c", MEDIUM: "#d97706", LOW: "#2563eb" };

const TILE_STYLES: Record<MapStyle, { label: string; url: string; attribution: string }> = {
  street: { label: "Street", url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png", attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>' },
  light: { label: "Light", url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png", attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>' },
  dark: { label: "Tactical", url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png", attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>' },
};

function MapController({ target, resizeNonce }: { target: MapTarget; resizeNonce: number }) {
  const map = useMap();
  useEffect(() => { map.flyTo(target.center, target.zoom, { duration: 1.1 }); }, [map, target]);
  useEffect(() => { const timeout = window.setTimeout(() => map.invalidateSize(), 160); return () => window.clearTimeout(timeout); }, [map, resizeNonce]);
  return null;
}

function DrawingEvents({ enabled, onPoint }: { enabled: boolean; onPoint: (point: GeoPoint) => void }) {
  useMapEvents({
    click: (event) => { if (enabled) onPoint({ latitude: event.latlng.lat, longitude: event.latlng.lng }); },
  });
  return null;
}

function zoneIcon(zone: CampusZone, selected: boolean) {
  const color = riskColor[zone.risk_level];
  return divIcon({
    className: "kiit-map-div-icon",
    html: `<button type="button" data-testid="map-hotspot-${zone.id}" aria-label="${zone.name}, ${zone.incidents} representative incidents" class="geo-marker ${zone.is_highest_risk ? "geo-marker-primary" : ""} ${selected ? "geo-marker-selected" : ""}" style="--marker-color:${color}"><span>${zone.incidents}</span></button>`,
    iconSize: L.point(42, 42),
    iconAnchor: L.point(21, 21),
  });
}

export default function KiitMap({ zones, incidents, selectedZoneId, onSelectZone, onSelectIncident, geofences, selectedGeofenceId, draftPoints, drawing, onAddDraftPoint, onSelectGeofence, onUndoDraft, onCancelDraft, onFinishDraft }: KiitMapProps) {
  const shellRef = useRef<HTMLDivElement>(null);
  const [target, setTarget] = useState<MapTarget>({ center: CITY, zoom: 12, nonce: 0 });
  const [style, setStyle] = useState<MapStyle>("light");
  const [query, setQuery] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [resizeNonce, setResizeNonce] = useState(0);
  const matches = useMemo(() => zones.filter((zone) => zone.name.toLowerCase().includes(query.trim().toLowerCase())).slice(0, 6), [query, zones]);

  const focus = (center: [number, number], zoom: number) => setTarget({ center, zoom, nonce: Date.now() });
  const chooseZone = (zone: CampusZone) => {
    setQuery(zone.name);
    setShowResults(false);
    focus([zone.latitude, zone.longitude], zone.scope === "KIIT" ? 16 : 14);
    onSelectZone(zone);
  };
  const toggleFullscreen = async () => {
    if (!shellRef.current) return;
    if (document.fullscreenElement) await document.exitFullscreen();
    else await shellRef.current.requestFullscreen();
    window.setTimeout(() => setResizeNonce((value) => value + 1), 180);
  };

  return (
    <div ref={shellRef} className={`map-shell map-style-${style} relative min-h-[620px] overflow-hidden rounded-2xl border border-slate-200 bg-slate-200`} data-testid="map-canvas">
      <MapContainer center={CITY as LatLngExpression} zoom={12} scrollWheelZoom zoomControl className="z-0 h-full min-h-[620px] w-full" aria-label="Bhubaneswar and KIIT incident map">
        <MapController target={target} resizeNonce={resizeNonce} />
        <DrawingEvents enabled={drawing} onPoint={onAddDraftPoint} />
        <TileLayer key={style} url={TILE_STYLES[style].url} attribution={TILE_STYLES[style].attribution} maxZoom={19} />
        {zones.map((zone) => (
          <Circle key={`zone-${zone.id}`} center={[zone.latitude, zone.longitude]} radius={zone.scope === "KIIT" ? Math.max(110, zone.incidents * 6) : Math.max(300, zone.incidents * 17)} pathOptions={{ color: riskColor[zone.risk_level], fillColor: riskColor[zone.risk_level], fillOpacity: zone.is_highest_risk ? 0.2 : 0.1, opacity: zone.is_highest_risk ? 0.8 : 0.42, weight: zone.is_highest_risk ? 3 : 1.5, dashArray: zone.is_highest_risk ? "6 5" : undefined }} eventHandlers={{ click: () => onSelectZone(zone) }}>
            <Tooltip direction="top" offset={[0, -14]}><strong>{zone.name}</strong><br />{zone.incidents} representative incidents · {zone.risk_level}</Tooltip>
          </Circle>
        ))}
        {zones.map((zone) => <Marker key={`marker-${zone.id}`} position={[zone.latitude, zone.longitude]} icon={zoneIcon(zone, selectedZoneId === zone.id)} eventHandlers={{ click: () => onSelectZone(zone) }} />)}
        {incidents.map((incident, index) => {
          const angle = index * 1.8;
          const latitude = incident.latitude + Math.sin(angle) * 0.0014;
          const longitude = incident.longitude + Math.cos(angle) * 0.0014;
          return <CircleMarker key={incident.id} center={[latitude, longitude]} radius={5} pathOptions={{ color: "#ffffff", fillColor: severityColor[incident.severity], fillOpacity: 0.95, opacity: 0.95, weight: 1.5 }} eventHandlers={{ click: () => onSelectIncident(incident) }}><Tooltip direction="top"><strong>{incident.title}</strong><br />{incident.status} · {incident.severity}</Tooltip></CircleMarker>;
        })}
        {geofences.map((geofence) => <Polygon key={geofence.id} positions={geofence.points.map((point) => [point.latitude, point.longitude] as [number, number])} pathOptions={{ color: selectedGeofenceId === geofence.id ? "#8b0000" : "#1e293b", fillColor: selectedGeofenceId === geofence.id ? "#c41e3a" : "#d97706", fillOpacity: selectedGeofenceId === geofence.id ? 0.2 : 0.1, weight: selectedGeofenceId === geofence.id ? 3 : 2, dashArray: "7 5" }} eventHandlers={{ click: () => onSelectGeofence(geofence) }}><Tooltip sticky><strong>{geofence.name}</strong><br />Risk score {geofence.stats.risk_score} · {geofence.stats.incident_count} incidents</Tooltip></Polygon>)}
        {drawing && draftPoints.length >= 2 && <Polygon positions={draftPoints.map((point) => [point.latitude, point.longitude] as [number, number])} pathOptions={{ color: "#8b0000", fillColor: "#c41e3a", fillOpacity: 0.22, weight: 3, dashArray: "5 4" }} />}
        {drawing && draftPoints.map((point, index) => <CircleMarker key={`${point.latitude}-${point.longitude}-${index}`} center={[point.latitude, point.longitude]} radius={5} pathOptions={{ color: "white", fillColor: "#8b0000", fillOpacity: 1, weight: 2 }} />)}
      </MapContainer>

      <div className="absolute left-4 right-16 top-4 z-[500] flex max-w-[680px] flex-col gap-2 sm:right-auto sm:w-[620px]" data-testid="map-search-panel">
        <div className="flex gap-2 rounded-xl border border-slate-200 bg-white/95 p-2 shadow-[0_12px_40px_rgba(15,23,42,0.18)] backdrop-blur-md">
          <div className="relative min-w-0 flex-1"><Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><Input data-testid="map-search-input" aria-label="Search Bhubaneswar or KIIT landmarks" value={query} onFocus={() => setShowResults(true)} onChange={(event) => { setQuery(event.target.value); setShowResults(true); }} placeholder="Search KIIT, KIMS, Patia, Station…" className="h-9 border-0 bg-slate-50 pl-10 text-sm text-slate-900 shadow-none placeholder:text-slate-400 focus-visible:ring-1" /></div>
          <Button type="button" data-testid="map-bhubaneswar-focus-button" variant="outline" className="hidden h-9 border-slate-200 bg-white text-slate-700 hover:bg-slate-100 sm:flex" onClick={() => focus(CITY, 12)}><Map className="size-4" /> City</Button>
          <Button type="button" data-testid="map-kiit-focus-button" className="h-9 bg-[#8b0000] text-white hover:bg-[#a30d1b]" onClick={() => focus(KIIT, 16)}><Building2 className="size-4" /> KIIT</Button>
        </div>
        {showResults && query.trim() && <div className="max-h-64 overflow-y-auto rounded-xl border border-slate-200 bg-white p-1.5 shadow-xl" data-testid="map-search-results">{matches.length ? matches.map((zone) => <button key={zone.id} type="button" data-testid={`map-search-result-${zone.id}`} onClick={() => chooseZone(zone)} className="flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left hover:bg-red-50"><span><span className="block text-sm font-semibold text-slate-800">{zone.name}</span><span className="mt-0.5 block text-[11px] text-slate-500">{zone.scope} · {zone.risk_level} risk</span></span><span className="font-mono text-xs font-semibold text-[#8b0000]">{zone.incidents}</span></button>) : <p className="px-3 py-4 text-sm text-slate-500">No predefined landmark found.</p>}</div>}
      </div>

      <div className="absolute bottom-8 left-4 z-[500] flex items-center gap-1 rounded-xl border border-slate-200 bg-white/95 p-1.5 shadow-lg backdrop-blur" data-testid="map-layer-controls">
        {(["street", "light", "dark"] as const).map((item) => <button key={item} type="button" data-testid={`map-layer-${item}-button`} aria-label={`Use ${TILE_STYLES[item].label} map`} onClick={() => setStyle(item)} className={`flex items-center gap-1.5 rounded-lg px-2.5 py-2 text-[10px] font-semibold uppercase tracking-wider ${style === item ? "bg-slate-900 text-white" : "text-slate-500 hover:bg-slate-100"}`}>{item === "street" ? <Map className="size-3.5" /> : item === "light" ? <SunMedium className="size-3.5" /> : <MoonStar className="size-3.5" />}<span className="hidden sm:inline">{TILE_STYLES[item].label}</span></button>)}
      </div>
      <div className="absolute bottom-8 right-4 z-[500] flex flex-col gap-2" data-testid="map-action-controls">
        <Button type="button" data-testid="map-locate-kiit-button" aria-label="Locate KIIT Square" variant="outline" size="icon" className="size-10 border-slate-200 bg-white text-[#8b0000] shadow-lg hover:bg-red-50" onClick={() => focus([20.3533, 85.8188], 17)}><LocateFixed className="size-4" /></Button>
        <Button type="button" data-testid="map-fullscreen-button" aria-label="Toggle map fullscreen" variant="outline" size="icon" className="size-10 border-slate-200 bg-white text-slate-700 shadow-lg hover:bg-slate-100" onClick={() => void toggleFullscreen()}><Expand className="size-4" /></Button>
      </div>
      {drawing && <div className="absolute left-1/2 top-24 z-[600] w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 rounded-xl border border-red-200 bg-white/95 p-3 shadow-2xl backdrop-blur" data-testid="geofence-drawing-toolbar"><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-xs font-bold text-slate-900">Draw patrol boundary</p><p className="mt-1 text-[10px] text-slate-500">Click at least 3 map points · {draftPoints.length} points added</p></div><div className="flex gap-1.5"><Button type="button" data-testid="geofence-undo-point-button" variant="outline" size="sm" disabled={!draftPoints.length} onClick={onUndoDraft}><RotateCcw className="size-3.5" /> Undo</Button><Button type="button" data-testid="geofence-cancel-draw-button" variant="outline" size="sm" onClick={onCancelDraft}><X className="size-3.5" /> Cancel</Button><Button type="button" data-testid="geofence-finish-draw-button" size="sm" disabled={draftPoints.length < 3} className="bg-[#8b0000] text-white hover:bg-[#a30d1b]" onClick={onFinishDraft}><Check className="size-3.5" /> Finish</Button></div></div></div>}
      <div className="absolute bottom-8 left-1/2 z-[450] hidden -translate-x-1/2 items-center gap-4 rounded-full border border-slate-700 bg-slate-900/92 px-4 py-2 text-[9px] font-mono uppercase tracking-wider text-slate-300 shadow-xl backdrop-blur lg:flex" data-testid="map-legend">
        {Object.entries(riskColor).map(([level, color]) => <span key={level} className="flex items-center gap-1.5"><span className="size-2 rounded-full" style={{ backgroundColor: color }} />{level}</span>)}
        <span className="border-l border-slate-700 pl-4 text-amber-300">Demo intelligence overlay</span>
      </div>
    </div>
  );
}