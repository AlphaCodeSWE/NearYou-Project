// dashboard-admin/frontend/src/services/ws.ts
type Message = {
    user_id: number;
    latitude: number;
    longitude: number;
    timestamp: string;
    age: number;
    profession: string;
    interests: string;
  };
  
  export function connectWS(
    onMessage: (msg: Message) => void
  ): WebSocket {
    const url = process.env.REACT_APP_WS_URL!;
    const ws = new WebSocket(url);
    ws.onmessage = e => {
      try {
        const msg: Message = JSON.parse(e.data);
        onMessage(msg);
      } catch {}
    };
    return ws;
  }
  