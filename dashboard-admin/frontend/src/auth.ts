// dashboard-admin/frontend/src/auth.ts
import axios from 'axios';

const TOKEN_KEY = 'ADMIN_TOKEN';
const AUTH_URL = process.env.REACT_APP_AUTH_URL!

export async function login(username: string, password: string) {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);
  const resp = await axios.post(
    `${AUTH_URL}/login`,
    params,
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
  );
  const token = resp.data.access_token as string;
  localStorage.setItem(TOKEN_KEY, token);
  return token;
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
