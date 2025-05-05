// dashboard-admin/frontend/src/services/api.ts
import axios from 'axios';
import { getToken } from '../auth';

const instance = axios.create({
  baseURL: process.env.REACT_APP_AUTH_URL,
});

instance.interceptors.request.use(cfg => {
  const t = getToken();
  if (t) cfg.headers!['Authorization'] = `Bearer ${t}`;
  return cfg;
});

export default instance;
