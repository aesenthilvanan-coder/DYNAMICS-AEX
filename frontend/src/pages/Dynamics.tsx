import { useState } from "react";
import { Link } from "react-router-dom";
import SimulationForm from "../components/dynamics/SimulationForm";
import AEXToggle from "../components/dynamics/AEXToggle";
import ProgressTracker from "../components/dynamics/ProgressTracker";
import OutputDownloader from "../components/dynamics/OutputDownloader";
import DynamicsSpotlight from "../components/dynamics/DynamicsSpotlight";
import type { DynamicsEstimate } from "../types/dynamics";
import { useQuery } from "@tanstack/react-query";
import { fetchDynamicsExecutionHealth, getLocalBootstrapScriptUrl } from "../api/dynamics";

export default function Dynamics() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [useAex, setUseAex] = useState(false);
  const [estimate, setEstimate] = useState<DynamicsEstimate | null>(null);

  const exec = useQuery({
    queryKey: ["dynamics-exec-health"],
    queryFn: fetchDynamicsExecutionHealth,
    refetchInterval: 30_000,
    retry: 1,
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-8">
        <Link
          to="/workspace"
          className="inline-flex text-xs font-semibold uppercase tracking-wider text-violet-300/80 hover:text-violet-200 border border-white/10 rounded-lg px-3 py-2 bg-white/[0.03]"
        >
          ← Workspace pipeline
        </Link>
        <span className="text-[10px] font-black uppercase tracking-[0.35em] text-emerald-400/90">
          This is the MD frontend
        </span>
      </div>

      <div className="mb-8">
        <DynamicsSpotlight variant="compact" />
      </div>

      <div className="mb-10 rounded-2xl border border-white/[0.08] bg-caly-graphite/20 p-6 sm:p-8">
        <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-white">
          <span className="text-emerald-400">DYNAMICS</span>{" "}
          <span className="text-caly-dim font-mono text-2xl sm:text-3xl font-bold">launcher</span>
        </h1>
        <p className="text-gray-300 mt-3 text-base sm:text-lg max-w-2xl">
          GROMACS molecular dynamics — upload files below, tune parameters, then submit. Optional AEX
          mode is toggled here.
        </p>
        <div className="flex flex-wrap gap-2 mt-5">
          <span className="text-xs font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-100 px-4 py-2 rounded-lg border border-emerald-400/40">
            GROMACS
          </span>
          {useAex && (
            <span className="text-xs font-bold uppercase tracking-wider bg-amber-900/50 text-amber-200 px-4 py-2 rounded-lg border border-amber-500/50">
              AEX on
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-gray-500">Execution readiness</div>
              <a
                href={getLocalBootstrapScriptUrl()}
                className="text-[10px] font-bold uppercase tracking-wider text-violet-300/90 hover:text-violet-200"
              >
                Download local setup script
              </a>
            </div>
            <div className="mt-3 text-sm text-gray-300">
              <div className="flex flex-wrap gap-x-6 gap-y-1">
                <span>
                  <span className="text-gray-500">GROMACS:</span>{" "}
                  <span className={exec.data?.gromacs ? "text-emerald-300" : "text-amber-300"}>
                    {exec.isPending ? "checking…" : exec.data?.gromacs ? "found" : "missing"}
                  </span>
                </span>
                <span>
                  <span className="text-gray-500">Broker:</span>{" "}
                  <span className={exec.data?.broker?.startsWith("ok") ? "text-emerald-300" : "text-amber-300"}>
                    {exec.isPending ? "checking…" : exec.data?.broker ?? "unknown"}
                  </span>
                </span>
                <span>
                  <span className="text-gray-500">Mode:</span>{" "}
                  <span className="text-gray-200">
                    {exec.data?.broker?.startsWith("ok") ? "Celery (recommended)" : "In-process fallback"}
                  </span>
                </span>
              </div>
              {!exec.isPending && exec.data && !exec.data.gromacs ? (
                <div className="mt-3 text-xs text-amber-200/90">
                  The backend can accept jobs, but it can’t actually run MD until GROMACS is installed in the backend
                  environment (Docker is the easiest path).
                </div>
              ) : null}
              {exec.isError ? (
                <div className="mt-3 text-xs text-red-300/90">
                  Couldn’t reach the backend readiness endpoint. Make sure the API is running on the configured base
                  URL.
                </div>
              ) : null}
            </div>
          </div>
          <div className="rounded-xl border-2 border-dashed border-emerald-500/35 bg-emerald-950/10 px-4 py-3">
            <p className="text-[11px] font-black uppercase tracking-[0.28em] text-emerald-200/90">
              Step 1 — configure & submit
            </p>
          </div>
          <AEXToggle value={useAex} onChange={setUseAex} />
          <SimulationForm
            useAex={useAex}
            onJobSubmitted={(id, est) => {
              setJobId(id);
              setEstimate(est as DynamicsEstimate);
            }}
          />
        </div>
        <div className="space-y-6">
          {estimate && (
            <div className="bg-white/5 rounded-xl p-5 border border-white/10">
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-4">Runtime estimate</div>
              <div className="space-y-3 text-sm">
                <EstRow
                  label="System atoms (est.)"
                  value={estimate.n_atoms_solvated_est?.toLocaleString()}
                />
                <EstRow label="Simulation time" value={`${estimate.sim_time_ns?.toFixed(2)} ns`} />
                <EstRow label="Hardware" value={estimate.hardware} />
                <EstRow label="Est. wall time" value={`${estimate.hours?.toFixed(1)} h`} />
                {useAex && (
                  <EstRow label="AEX speedup" value={`${estimate.aex_speedup?.toFixed(1)}×`} highlight />
                )}
              </div>
            </div>
          )}
          {jobId && (
            <>
              <ProgressTracker jobId={jobId} />
              <OutputDownloader jobId={jobId} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function EstRow({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value?: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-gray-500 shrink-0">{label}</span>
      <span className={highlight ? "text-amber-400 font-semibold text-right" : "text-white text-right"}>
        {value ?? "—"}
      </span>
    </div>
  );
}
