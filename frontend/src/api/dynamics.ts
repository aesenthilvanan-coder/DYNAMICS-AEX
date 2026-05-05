import { apiClient } from "./client";
import type { JobStatusResponse } from "../types/dynamics";

export interface DynamicsExecutionHealth {
  gromacs: string | null;
  broker: string;
  inprocess_jobs: number;
}

export async function submitDynamicsJob(formData: FormData) {
  const { data } = await apiClient.post("/dynamics/submit", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data as { job_id: string; status: string; estimate?: Record<string, unknown>; mode?: string };
}

export async function pollJobStatus(jobId: string): Promise<JobStatusResponse> {
  const { data } = await apiClient.get<JobStatusResponse>(`/dynamics/jobs/${jobId}`);
  return data;
}

export async function getAEXReport(jobId: string) {
  const { data } = await apiClient.get(`/dynamics/jobs/${jobId}/aex-report`);
  return data;
}

export function getDownloadUrl(jobId: string): string {
  const base = apiClient.defaults.baseURL || "";
  return `${base}/dynamics/jobs/${jobId}/download`;
}

export async function fetchLocalBootstrapManifest(): Promise<Record<string, unknown>> {
  const { data } = await apiClient.get<Record<string, unknown>>("/dynamics/local-bootstrap.json");
  return data;
}

export async function fetchDynamicsExecutionHealth(): Promise<DynamicsExecutionHealth> {
  const { data } = await apiClient.get<DynamicsExecutionHealth>("/dynamics/health-execution");
  return data;
}

export function getLocalBootstrapScriptUrl(): string {
  const base = apiClient.defaults.baseURL || "";
  return `${base}/dynamics/local-bootstrap.sh`;
}
