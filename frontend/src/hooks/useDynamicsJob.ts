import { useQuery } from "@tanstack/react-query";
import { pollJobStatus } from "../api/dynamics";
import type { JobStatusResponse } from "../types/dynamics";

export function useDynamicsJob(jobId: string | null) {
  return useQuery<JobStatusResponse>({
    queryKey: ["dynamics-job", jobId],
    enabled: !!jobId,
    queryFn: () => pollJobStatus(jobId!),
    refetchInterval: (q) =>
      q.state.data?.status === "pending" || q.state.data?.status === "running" ? 3000 : false,
  });
}
