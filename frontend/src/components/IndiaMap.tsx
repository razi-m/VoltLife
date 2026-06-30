/**
 * IndiaMap.tsx — marketplace supplier discovery map (react-leaflet + OpenStreetMap, no tokens).
 *
 * SETUP (run locally — this sandbox cannot install/build):
 *   cd frontend && npm install react-leaflet@^4.2.1 leaflet@^1.9.4
 *   then import 'leaflet/dist/leaflet.css' (here or in index.html)
 *
 * Wire into the marketplace discovery page:
 *   import IndiaMap from '../components/IndiaMap';
 *   <IndiaMap onSelectSupplier={(id) => navigate(`/shop/seller/${id}`)} />
 *
 * Data: GET /api/v1/marketplace/suppliers. Suppliers currently have NO lat/lng, so we geocode
 * by the city parsed from `address` (demo-grade). If you later add nullable lat/lng to the
 * Supplier model + seed real coords, prefer those over the city lookup.
 */
import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix default marker icons under bundlers (Vite) — leaflet's images aren't resolved automatically.
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
const DefaultIcon = L.icon({ iconUrl: markerIcon, shadowUrl: markerShadow, iconSize: [25, 41], iconAnchor: [12, 41] });
L.Marker.prototype.options.icon = DefaultIcon;

const API_BASE = (import.meta as any).env?.VITE_API_URL || ((import.meta as any).env?.PROD ? '' : 'http://localhost:8000');

// City -> [lat, lng] (covers the seed cities; falls back to India centroid).
const CITY_COORDS: Record<string, [number, number]> = {
  Pune: [18.52, 73.85], Mumbai: [19.07, 72.88], Chennai: [13.08, 80.27],
  Bengaluru: [12.97, 77.59], Bangalore: [12.97, 77.59], Hyderabad: [17.39, 78.49],
  Delhi: [28.61, 77.21], Ahmedabad: [23.02, 72.57], Jaipur: [26.91, 75.79],
  Kolkata: [22.57, 88.36], Lucknow: [26.85, 80.95], Bhopal: [23.26, 77.41],
  Coimbatore: [11.02, 76.96], Nagpur: [21.15, 79.09], Surat: [21.17, 72.83],
  Patna: [25.59, 85.14], Kochi: [9.93, 76.27],
};
const INDIA_CENTER: [number, number] = [22.97, 78.65];

function geocode(address = ''): [number, number] {
  for (const city in CITY_COORDS) if (address.includes(city)) return CITY_COORDS[city];
  return INDIA_CENTER;
}

interface Supplier { id: number; company_name: string; address?: string; phone?: string; email?: string; }

export default function IndiaMap({ onSelectSupplier }: { onSelectSupplier?: (id: number) => void }) {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/marketplace/suppliers`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('failed'))))
      .then((data) => setSuppliers(Array.isArray(data) ? data : []))
      .catch(() => setError('Could not load suppliers'));
  }, []);

  return (
    <div style={{ width: '100%' }}>
      {error && <div className="map-error">{error}</div>}
      <MapContainer center={INDIA_CENTER} zoom={5} scrollWheelZoom style={{ height: '480px', width: '100%', borderRadius: 12 }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {suppliers.map((sup) => {
          const [lat, lng] = geocode(sup.address || '');
          return (
            <Marker key={sup.id} position={[lat, lng]}>
              <Popup>
                <strong>{sup.company_name}</strong>
                <br />{sup.address || 'India'}
                <br />
                <button onClick={() => onSelectSupplier?.(sup.id)} style={{ marginTop: 6 }}>
                  View supplier profile
                </button>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
