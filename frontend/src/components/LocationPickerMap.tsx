import { useEffect } from "react";
import L, { divIcon } from "leaflet";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";
import { LocateFixed } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { GeoPoint } from "@/lib/types";

const KIIT_CENTER: [number, number] = [20.3533, 85.8188];
const incidentIcon = divIcon({ className: "report-location-icon", html: '<span data-testid="report-location-pin"></span>', iconSize: L.point(28, 28), iconAnchor: L.point(14, 28) });

function ClickPicker({ onChange }: { onChange: (point: GeoPoint) => void }) {
  useMapEvents({ click: (event) => onChange({ latitude: event.latlng.lat, longitude: event.latlng.lng }) });
  return null;
}

function Recenter({ value }: { value: GeoPoint }) {
  const map = useMap();
  useEffect(() => { map.flyTo([value.latitude, value.longitude], Math.max(map.getZoom(), 15), { duration: 0.8 }); }, [map, value]);
  return null;
}

export default function LocationPickerMap({ value, onChange }: { value: GeoPoint; onChange: (point: GeoPoint) => void }) {
  const useMyLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((position) => onChange({ latitude: position.coords.latitude, longitude: position.coords.longitude }));
  };
  return <div className="relative overflow-hidden rounded-xl border border-slate-200" data-testid="report-location-map"><MapContainer center={KIIT_CENTER} zoom={15} scrollWheelZoom className="h-72 w-full"><TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>' /><ClickPicker onChange={onChange} /><Recenter value={value} /><Marker position={[value.latitude, value.longitude]} icon={incidentIcon} /></MapContainer><Button type="button" data-testid="report-use-location-button" variant="outline" size="sm" className="absolute right-3 top-3 z-[500] border-slate-200 bg-white text-slate-700 shadow-lg hover:bg-slate-50" onClick={useMyLocation}><LocateFixed className="size-3.5" /> Use my location</Button><p className="absolute bottom-5 left-3 z-[500] rounded-md bg-slate-900/85 px-2 py-1 font-mono text-[8px] text-white" data-testid="report-location-coordinates">{value.latitude.toFixed(5)}, {value.longitude.toFixed(5)}</p></div>;
}