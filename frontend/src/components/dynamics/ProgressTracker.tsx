import { motion } from "framer-motion";
import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { useDynamicsJob } from "../../hooks/useDynamicsJob";

export default function ProgressTracker({ jobId }: { jobId: string }) {
  const q = useDynamicsJob(jobId);
  const [open, setOpen] = useState(false);
  if (!jobId) return null;
  const st = q.data?.status ?? "pending";
  const pct = q.data?.progress ?? 0;
  const done = st === "complete" || st === "failed";

  return (
    <div className="rounded-xl border border-white/[0.08] bg-caly-graphite/50 p-5 shadow-spectral-inset">
      <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-caly-dim mb-2">Job status</div>
      <div className="text-xs font-mono text-caly-mist mb-1 break-all">{jobId}</div>
      <div className="flex items-center justify-between gap-2 mb-3">
        <span className="text-sm text-caly-mist capitalize">{st}</span>
        <span className="text-xs font-mono text-caly-dim">{pct}%</span>
      </div>
      <div className="h-2 rounded-full bg-caly-void overflow-hidden border border-white/[0.06]">
        <motion.div
          className="h-full rounded-full"
          initial={false}
          animate={{ width: `${pct}%` }}
          transition={{ type: "spring", stiffness: 120, damping: 20 }}
          style={{
            background:
              st === "failed"
                ? "linear-gradient(90deg, #f87171, #fb923c)"
                : "linear-gradient(90deg, #a78bfa, #4dfff0, #6b8cff)",
            boxShadow: done ? undefined : "0 0 12px rgba(167,139,250,0.35)",
          }}
        />
      </div>
      {q.data?.current_step ? (
        <div className="text-xs text-caly-dim mt-2 font-mono">{q.data.current_step}</div>
      ) : null}
      {q.data?.error ? (
        <div className="text-xs text-red-400/90 mt-2">{q.data.error}</div>
      ) : null}

      {q.data?.result != null && (
        <div className="mt-4 border-t border-white/[0.06] pt-3">
          <button
            type="button"
            onClick={() => setOpen(!open)}
            className="flex w-full items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-caly-dim hover:text-caly-mist"
          >
            Result payload
            <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
          {open && (
            <pre className="mt-2 text-[10px] font-mono text-caly-dim max-h-48 overflow-auto rounded border border-white/[0.06] p-2 bg-black/40">
              {JSON.stringify(q.data.result, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
