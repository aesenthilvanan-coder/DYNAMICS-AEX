interface Props {
  value: boolean;
  onChange: (v: boolean) => void;
}

export default function AEXToggle({ value, onChange }: Props) {
  return (
    <label
      className={[
        "flex items-center justify-between rounded-xl border px-4 py-3.5 cursor-pointer transition-all",
        value
          ? "border-violet-500/35 bg-gradient-to-r from-violet-500/[0.08] to-cyan-500/[0.05] shadow-spectral"
          : "border-white/[0.08] bg-caly-void/40 hover:border-white/12",
      ].join(" ")}
    >
      <div>
        <div className="text-sm font-semibold text-caly-mist">AEX adaptive execution</div>
        <div className="text-xs text-caly-dim mt-0.5">
          Stability-gated segments · requires GROMACS toolchain
        </div>
      </div>
      <div className="relative">
        <input
          type="checkbox"
          checked={value}
          onChange={(e) => onChange(e.target.checked)}
          className="peer sr-only"
        />
        <span
          className={[
            "block h-6 w-11 rounded-full border transition-colors",
            value ? "bg-violet-500/30 border-violet-400/40" : "bg-caly-graphite border-white/15",
          ].join(" ")}
        />
        <span
          className={[
            "absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-caly-mist transition-transform shadow-md",
            value ? "translate-x-5" : "translate-x-0",
          ].join(" ")}
        />
      </div>
    </label>
  );
}
