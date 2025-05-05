// dashboard-admin/frontend/src/pages/Login.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../auth';

export default function Login() {
  const [u, setU] = useState('');
  const [p, setP] = useState('');
  const [err, setErr] = useState('');
  const nav = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(u, p);
      nav('/map');
    } catch {
      setErr('Credenziali errate');
    }
  };

  return (
    <div style={{ maxWidth: 300, margin: '100px auto' }}>
      <h2>Admin Login</h2>
      <form onSubmit={submit}>
        <input
          value={u}
          onChange={e => setU(e.target.value)}
          placeholder="Username"
          required
        /><br/>
        <input
          type="password"
          value={p}
          onChange={e => setP(e.target.value)}
          placeholder="Password"
          required
        /><br/>
        <button type="submit">Login</button>
      </form>
      {err && <p style={{ color: 'red' }}>{err}</p>}
    </div>
  );
}
