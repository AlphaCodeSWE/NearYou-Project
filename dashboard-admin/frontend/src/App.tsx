// dashboard-admin/frontend/src/App.tsx
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { getToken } from './auth';
import Login from './pages/Login';
import AdminMap from './pages/AdminMap';
import Analytics from './pages/Analytics';

function PrivateRoute({ children }: { children: JSX.Element }) {
  return getToken() ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/map"
        element={
          <PrivateRoute>
            <AdminMap />
          </PrivateRoute>
        }
      />
      <Route
        path="/analytics"
        element={
          <PrivateRoute>
            <Analytics />
          </PrivateRoute>
        }
      />
      <Route path="*" element={<Navigate to="/map" />} />
    </Routes>
  );
}
