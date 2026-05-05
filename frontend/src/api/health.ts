import axios from "axios";

export function getPublicApiOrigin(): string {
  const configured = import.meta.env.VITE_API_URL;
  if (configured) {
    return configured.replace(/\/api\/v1\/?$/, "");
  }
  if (import.meta.env.DEV) {
    return "http://localhost:8000";
  }
  return "";
}

export interface HealthResponse {
  status: string;
  version?: string;
  database?: string;
  storage_backend?: string;
  gromacs_bin?: string;
  module?: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const origin = getPublicApiOrigin();
  const { data } = await axios.get<HealthResponse>(`${origin}/health`, { timeout: 15000 });
  return data;
}
