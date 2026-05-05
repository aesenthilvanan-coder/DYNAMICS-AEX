import { useQuery } from "@tanstack/react-query";
import { fetchHealth } from "../../api/health";

type State = "yes" | "no" | "warn" | "idle";

function statusDot(s: State) {
  if (s === "yes") return "bg-emerald-500";
  if (s === "no") return "bg-red-500";
  if (s === "warn") return "bg-amber-500";
  return "bg-gray-600";
}

export default function BackendStatus() {
  const { data, isError, isPending } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 60_000,
    retry: 1,
  });

  let api: State = "idle";
  if (!isPending) {
    if (isError || !data) api = "no";
    else if (data.status === "ok") api = "yes";
    else if (data.status === "degraded") api = "warn";
    else api = "no";
  }

  const dbStr = data?.database ?? "";
  let db: State = "idle";
  if (!isPending && data) {
    if (dbStr === "ok" || dbStr === "disabled") db = "yes";
    else if (dbStr.startsWith("error")) db = "no";
    else db = "warn";
  }

  return (
    <div className="flex items-center gap-3 text-xs text-gray-500">
      <span className="flex items-center gap-1.5" title="GET /health">
        <span className={`h-2 w-2 rounded-full ${statusDot(api)}`} />
        API
      </span>
      <span className="flex items-center gap-1.5" title={dbStr || "database"}>
        <span className={`h-2 w-2 rounded-full ${statusDot(db)}`} />
        DB
      </span>
      {data?.storage_backend && (
        <span className="hidden md:inline text-gray-600">· {data.storage_backend}</span>
      )}
    </div>
  );
}
