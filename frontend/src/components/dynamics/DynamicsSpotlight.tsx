import { Link } from "react-router-dom";
import { Atom, ArrowRight, FlaskConical } from "lucide-react";

type Variant = "landing" | "compact";

/**
 * High-visibility entry to the DYNAMICS / GROMACS UI — used on landing and inside MD pages.
 */
export default function DynamicsSpotlight({ variant = "landing" }: { variant?: Variant }) {
  const isCompact = variant === "compact";

  return (
    <section
      className={[
        "relative overflow-hidden rounded-2xl border-2 border-emerald-400/50 bg-gradient-to-br from-emerald-950/80 via-caly-graphite to-teal-950/60",
        "shadow-[0_0_80px_-20px_rgba(52,211,153,0.45)]",
        isCompact ? "p-5 sm:p-6" : "p-8 sm:p-12 text-center",
      ].join(" ")}
      aria-labelledby="dynamics-spotlight-title"
    >
      <div
        className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-emerald-400/10 blur-3xl"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -bottom-16 -left-16 h-48 w-48 rounded-full bg-cyan-400/10 blur-3xl"
        aria-hidden
      />

      <div className={isCompact ? "relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4" : "relative max-w-3xl mx-auto"}>
        <div className={isCompact ? "min-w-0" : ""}>
          <p className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.35em] text-emerald-300">
            <FlaskConical className="h-4 w-4 text-emerald-200 shrink-0" strokeWidth={2} />
            Molecular dynamics · frontend
          </p>
          <h2
            id="dynamics-spotlight-title"
            className={[
              "font-bold text-white tracking-tight text-balance mt-2",
              isCompact ? "text-xl sm:text-2xl" : "text-3xl sm:text-4xl md:text-5xl",
            ].join(" ")}
          >
            Simulate proteins in GROMACS — obvious controls, one screen
          </h2>
          {!isCompact && (
            <p className="mt-4 text-base sm:text-lg text-emerald-100/80 leading-relaxed">
              Upload PDB, optional ligand topology, hit submit. Optional AEX acceleration. Outputs zip
              when the worker finishes.
            </p>
          )}
        </div>

        <div
          className={[
            "flex flex-col sm:flex-row gap-3 shrink-0",
            isCompact ? "sm:justify-end" : "mt-8 justify-center flex-wrap",
          ].join(" ")}
        >
          <Link
            to="/dynamics"
            className="group inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-6 sm:px-8 py-4 text-base font-bold text-emerald-950 shadow-lg shadow-emerald-500/25 hover:bg-emerald-400 transition-colors border border-emerald-300/50"
          >
            <Atom className="h-5 w-5 shrink-0" strokeWidth={2.5} />
            OPEN DYNAMICS
            <ArrowRight className="h-5 w-5 opacity-80 group-hover:translate-x-0.5 transition-transform" />
          </Link>
          <Link
            to="/workspace#ws-dynamics"
            className="inline-flex items-center justify-center gap-2 rounded-xl border-2 border-white/25 bg-white/10 px-5 py-4 text-sm font-semibold text-white hover:bg-white/15 transition-colors"
          >
            Pipeline workspace
            <span className="text-[10px] font-mono uppercase text-white/60">jump to MD</span>
          </Link>
        </div>
      </div>
    </section>
  );
}
