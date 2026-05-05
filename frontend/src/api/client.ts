import axios from "axios";

const base =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? "/api/v1" : "http://localhost:8000/api/v1");

export const apiClient = axios.create({
  baseURL: base,
  timeout: 120000,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail ?? err.message ?? "Unknown error";
    const text = typeof msg === "string" ? msg : JSON.stringify(msg);
    return Promise.reject(new Error(text));
  }
);
