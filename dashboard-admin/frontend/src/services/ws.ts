import { getToken } from '../auth';
import type { Point } from '../components/Map';

export function connectWS(onMessage: (pt: Point) => void): WebSocket {
  const token = getToken();
  // passiamo il token come subprotocollo per aggirare il divieto di header custom
  const ws = new WebSocket(
    `${process.env.REACT_APP_WS_URL}/ws`,
    token ? [`Bearer ${token}`] : []
  );
  ws.onmessage = ev => {
    const data = JSON.parse(ev.data) as Point;
    onMessage(data);
  };
  ws.onerror = err => console.error('WS error', err);
  return ws;
}
