// dashboard-admin/frontend/src/pages/AdminMap.tsx
import React, { useState, useEffect, useRef } from 'react';
import { connectWS } from '../services/ws';
import Map, { Point } from '../components/Map';
import { logout } from '../auth';
import { useNavigate } from 'react-router-dom';

export default function AdminMap() {
  const [pts, setPts] = useState<Point[]>([]);
  const [minAge, setMinAge] = useState(0);
  const wsRef = useRef<WebSocket>();
  const nav = useNavigate();

  useEffect(() => {
    wsRef.current = connectWS(msg => {
      setPts(old => [...old, msg].filter(p => p.age >= minAge));
    });
    return () => wsRef.current?.close();
  }, [minAge]);

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ padding: 10, background: '#eee' }}>
        <button onClick={() => { logout(); nav('/login'); }}>
          Logout
        </button>
        {' '}
        Min Age:{' '}
        <input
          type="number"
          value={minAge}
          onChange={e => setMinAge(+e.target.value)}
          style={{ width: 60 }}
        />
        {' '}
        <a href="/analytics" style={{ marginLeft: 20 }}>Analytics</a>
      </header>
      <div style={{ flex: 1 }}>
        <Map points={pts} />
      </div>
    </div>
  );
}
