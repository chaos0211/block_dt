// src/api/http.ts
import axios from "axios";

// 后端默认 http://localhost:8000
// const baseURL = (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000";

const http = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 15000,
});

// 请求拦截器：自动附加 JWT
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers = config.headers || {};
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：处理未认证错误
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
    }
    return Promise.reject(error);
  }
);

export default http;