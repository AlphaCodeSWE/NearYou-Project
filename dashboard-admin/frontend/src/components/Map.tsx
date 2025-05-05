// dashboard-admin/frontend/src/components/Map.tsx
import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

interface MapProps {
  center: [number, number];
  zoom?: number;
  children?: React.ReactNode;
}

const Map: React.FC<MapProps> = ({
  center,
  zoom = 13,
  children
}) => {
  return (
    <MapContainer
      center={center}
      zoom={zoom}
      style={{ height: '100%', width: '100%' }}
    >
      {/* OpenStreetMap tile layer */}
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution={`
          © <a href="https://www.openstreetmap.org/copyright">
            OpenStreetMap
          </a> contributors
        `}
      />

      {children}
    </MapContainer>
  );
};

export default Map;
