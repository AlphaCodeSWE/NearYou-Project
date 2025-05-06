import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

/** GeoJSON-like point coming from WS */
export interface Point {
  geometry: {
    type: 'Point';
    coordinates: [number, number]; // [lon, lat]
  };
  properties: { [key: string]: any };
}

interface MapProps {
  /** coordinate [lat, lon] del centro; default Milano */
  center?: [number, number];
  zoom?: number;
  /** elenco di punti da mettere come Marker */
  points: Point[];
}

const Map: React.FC<MapProps> = ({
  center = [45.4642, 9.19],
  zoom = 13,
  points
}) => (
  <MapContainer center={center} zoom={zoom} style={{ height: '100%', width: '100%' }}>
    <TileLayer
      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      attribution="© OpenStreetMap contributors"
    />
    {points.map((pt, i) => (
      <Marker
        key={i}
        // Leaflet vuole [lat, lon]
        position={[pt.geometry.coordinates[1], pt.geometry.coordinates[0]]}
      >
        <Popup>
          {Object.entries(pt.properties).map(([k, v]) => (
            <div key={k}>
              <strong>{k}:</strong> {String(v)}
            </div>
          ))}
        </Popup>
      </Marker>
    ))}
  </MapContainer>
);

export default Map;
