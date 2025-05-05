// dashboard-admin/frontend/src/pages/Analytics.tsx
import React from 'react';

export default function Analytics() {
  const url = process.env.REACT_APP_GRAFANA_URL! +
    '/d/your-dashboard-uid?orgId=1&kiosk';

  return (
    <iframe
      src={url}
      style={{ border: 0, width: '100%', height: '100vh' }}
      title="Grafana Analytics"
    />
  );
}
