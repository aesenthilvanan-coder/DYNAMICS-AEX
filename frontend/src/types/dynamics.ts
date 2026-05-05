export interface DynamicsEstimate {
  n_atoms_protein?: number;
  n_atoms_solvated_est?: number;
  hardware?: string;
  sim_time_ns?: number;
  hours?: number;
  aex_speedup?: number;
}

export interface JobStatusResponse {
  job_id: string;
  status: string;
  progress: number;
  current_step?: string;
  result?: Record<string, unknown> | null;
  error?: string | null;
}
