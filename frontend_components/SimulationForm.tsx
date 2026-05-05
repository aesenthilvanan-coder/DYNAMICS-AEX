import React, { useState, useRef, useEffect } from "react";
import { submitDynamicsJob } from "../../api/dynamics";

interface SimulationFormProps {
  useAex: boolean;
  onJobSubmitted: (jobId: string, estimate: unknown) => void;
  onFileStateChange?: (s: { hasPdb: boolean; hasItp: boolean; hasMol2: boolean }) => void;
  className?: string;
}

export default function SimulationForm({
  useAex,
  onJobSubmitted,
  onFileStateChange,
  className = "",
}: SimulationFormProps) {
  const [loading, setLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const pdbRef = useRef<HTMLInputElement>(null);
  const itpRef = useRef<HTMLInputElement>(null);
  const mol2Ref = useRef<HTMLInputElement>(null);

  const emitFiles = () => {
    onFileStateChange?.({
      hasPdb: !!pdbRef.current?.files?.length,
      hasItp: !!itpRef.current?.files?.length,
      hasMol2: !!mol2Ref.current?.files?.length,
    });
  };

  useEffect(() => {
    emitFiles();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- refs only
  }, []);

  const [params, setParams] = useState({
    forcefield: "amber99sb-ildn",
    water_model: "tip3p",
    box_type: "dodecahedron",
    box_distance: 1.0,
    temperature: 300.0,
    pressure: 1.0,
    dt: 0.002,
    production_steps: 5000000,
    nvt_steps: 100000,
    npt_steps: 100000,
    em_steps: 50000,
    thermostat: "v-rescale",
    barostat: "Parrinello-Rahman",
    tau_t: 0.1,
    tau_p: 2.0,
    coulombtype: "PME",
    rcoulomb: 1.0,
    rvdw: 1.0,
    fourierspacing: 0.16,
    constraints: "h-bonds",
    lincs_iter: 1,
    lincs_order: 4,
    nstxout: 500,
    nstvout: 500,
    nstfout: 0,
    nstxout_compressed: 500,
    nstenergy: 500,
    nstlog: 500,
    posre: true,
    gen_vel: true,
    continuation: false,
    aex_fidelity_target: 0.95,
    aex_max_speedup: 10.0,
    custom_mdp_overrides: {} as Record<string, string | number>,
  });

  const handleSubmit = async () => {
    const pdbFile = pdbRef.current?.files?.[0];
    if (!pdbFile) {
      window.alert("Please upload a PDB file");
      return;
    }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("protein_pdb", pdbFile);
      const itpFile = itpRef.current?.files?.[0];
      if (itpFile) formData.append("ligand_itp", itpFile);
      const mol2File = mol2Ref.current?.files?.[0];
      if (mol2File) formData.append("ligand_mol2", mol2File);
      formData.append("params", JSON.stringify({ ...params, use_aex: useAex }));
      const result = await submitDynamicsJob(formData);
      onJobSubmitted(result.job_id, result.estimate);
    } catch (e: unknown) {
      window.alert(`Submission failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
    }
  };

  const update = (key: string, value: unknown) => setParams((p) => ({ ...p, [key]: value }));

  return (
    <div
      className={`bg-white/[0.03] rounded-xl border border-white/[0.08] p-6 space-y-6 ${className}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm font-black text-white uppercase tracking-[0.2em]">
          Simulation parameters
        </div>
        <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-300/90 border border-emerald-500/40 rounded-md px-2 py-1 bg-emerald-500/10">
          MD job form
        </span>
      </div>
      <Section title="Input Files">
        <FileInput label="Protein PDB *" ref={pdbRef} accept=".pdb" onFileChange={emitFiles} />
        <FileInput label="Ligand ITP (optional)" ref={itpRef} accept=".itp" onFileChange={emitFiles} />
        <FileInput
          label="Ligand MOL2 (optional, with ITP for topology integration)"
          ref={mol2Ref}
          accept=".mol2"
          onFileChange={emitFiles}
        />
      </Section>
      <Section title="System Setup">
        <SelectField
          label="Force field"
          value={params.forcefield}
          onChange={(v) => update("forcefield", v)}
          options={["amber99sb-ildn", "charmm36m", "gromos54a7", "oplsaa"]}
        />
        <SelectField
          label="Water model"
          value={params.water_model}
          onChange={(v) => update("water_model", v)}
          options={["tip3p", "tip4p", "tip5p", "spc/e"]}
        />
        <SelectField
          label="Box type"
          value={params.box_type}
          onChange={(v) => update("box_type", v)}
          options={["dodecahedron", "cubic", "octahedron"]}
        />
        <NumberField
          label="Box distance (nm)"
          value={params.box_distance}
          onChange={(v) => update("box_distance", v)}
          min={0.8}
          max={2.0}
          step={0.1}
        />
      </Section>
      <Section title="Simulation Conditions">
        <NumberField
          label="Temperature (K)"
          value={params.temperature}
          onChange={(v) => update("temperature", v)}
          min={270}
          max={370}
          step={5}
        />
        <NumberField
          label="Pressure (bar)"
          value={params.pressure}
          onChange={(v) => update("pressure", v)}
          min={0.5}
          max={2.0}
          step={0.1}
        />
        <SelectField
          label="Thermostat"
          value={params.thermostat}
          onChange={(v) => update("thermostat", v)}
          options={["v-rescale", "nose-hoover", "berendsen"]}
        />
        <SelectField
          label="Barostat"
          value={params.barostat}
          onChange={(v) => update("barostat", v)}
          options={["Parrinello-Rahman", "Berendsen", "MTTK"]}
        />
        <NumberField
          label="Thermostat τ_t (ps)"
          value={params.tau_t}
          onChange={(v) => update("tau_t", v)}
          min={0.01}
          max={5.0}
          step={0.05}
        />
        <NumberField
          label="Barostat τ_p (ps)"
          value={params.tau_p}
          onChange={(v) => update("tau_p", v)}
          min={0.1}
          max={10.0}
          step={0.1}
        />
      </Section>
      <Section title="Simulation Length">
        <NumberField
          label="Timestep (ps)"
          value={params.dt}
          onChange={(v) => update("dt", v)}
          min={0.001}
          max={0.004}
          step={0.001}
        />
        <div className="text-xs text-gray-500">
          Production: {((params.production_steps * params.dt) / 1000).toFixed(1)} ns · Total:{" "}
          {(((params.production_steps + params.nvt_steps + params.npt_steps) * params.dt) / 1000).toFixed(
            1
          )}{" "}
          ns
        </div>
        <NumberField
          label="Production steps"
          value={params.production_steps}
          onChange={(v) => update("production_steps", v)}
          min={100000}
          step={100000}
        />
        <NumberField
          label="NVT steps"
          value={params.nvt_steps}
          onChange={(v) => update("nvt_steps", v)}
          min={10000}
          step={10000}
        />
        <NumberField
          label="NPT steps"
          value={params.npt_steps}
          onChange={(v) => update("npt_steps", v)}
          min={10000}
          step={10000}
        />
        <NumberField
          label="EM steps"
          value={params.em_steps}
          onChange={(v) => update("em_steps", v)}
          min={1000}
          step={10000}
        />
      </Section>
      {useAex && (
        <Section title="AEX Parameters">
          <NumberField
            label="Fidelity target"
            value={params.aex_fidelity_target}
            onChange={(v) => update("aex_fidelity_target", v)}
            min={0.9}
            max={0.99}
            step={0.01}
          />
          <NumberField
            label="Max speedup (×)"
            value={params.aex_max_speedup}
            onChange={(v) => update("aex_max_speedup", v)}
            min={2}
            max={20}
            step={1}
          />
        </Section>
      )}
      <Section title="Output Frequency">
        <NumberField
          label="Coords output (steps)"
          value={params.nstxout}
          onChange={(v) => update("nstxout", v)}
          min={0}
          step={100}
        />
        <NumberField
          label="Velocities output (steps)"
          value={params.nstvout}
          onChange={(v) => update("nstvout", v)}
          min={0}
          step={100}
        />
        <NumberField
          label="Forces output (steps)"
          value={params.nstfout}
          onChange={(v) => update("nstfout", v)}
          min={0}
          step={100}
        />
        <NumberField
          label="Trajectory output (steps)"
          value={params.nstxout_compressed}
          onChange={(v) => update("nstxout_compressed", v)}
          min={100}
          step={100}
        />
        <NumberField
          label="Energy output (steps)"
          value={params.nstenergy}
          onChange={(v) => update("nstenergy", v)}
          min={100}
          step={100}
        />
      </Section>

      <div className="rounded-lg border border-white/[0.08] bg-black/20 px-4 py-3">
        <button
          type="button"
          onClick={() => setShowAdvanced((v) => !v)}
          className="w-full flex items-center justify-between text-[10px] font-bold uppercase tracking-[0.25em] text-gray-400 hover:text-gray-200"
        >
          Advanced (full DynamicsInputs)
          <span className="text-gray-500">{showAdvanced ? "Hide" : "Show"}</span>
        </button>
        {showAdvanced && (
          <div className="mt-4 space-y-6">
            <Section title="Electrostatics & constraints">
              <NumberField
                label="Fourier spacing (nm)"
                value={params.fourierspacing}
                onChange={(v) => update("fourierspacing", v)}
                min={0.08}
                max={0.3}
                step={0.01}
              />
              <NumberField
                label="LINCS iterations"
                value={params.lincs_iter}
                onChange={(v) => update("lincs_iter", v)}
                min={1}
                max={8}
                step={1}
              />
              <NumberField
                label="LINCS order"
                value={params.lincs_order}
                onChange={(v) => update("lincs_order", v)}
                min={1}
                max={12}
                step={1}
              />
            </Section>

            <Section title="Protocol toggles">
              <ToggleField
                label="Position restraints during equilibration"
                value={params.posre}
                onChange={(v) => update("posre", v)}
              />
              <ToggleField label="Generate velocities" value={params.gen_vel} onChange={(v) => update("gen_vel", v)} />
              <ToggleField label="Continuation mode" value={params.continuation} onChange={(v) => update("continuation", v)} />
              <div className="text-[11px] text-gray-500">
                These map directly onto `DynamicsInputs.posre`, `gen_vel`, and `continuation`.
              </div>
            </Section>

            <Section title="Custom MDP overrides (JSON)">
              <textarea
                value={JSON.stringify(params.custom_mdp_overrides ?? {}, null, 2)}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value || "{}");
                    setParams((p) => ({ ...p, custom_mdp_overrides: parsed }));
                  } catch {
                    // keep text edits; submit-time parse will still be JSON in params
                    // (no-op to avoid noisy typing errors)
                  }
                }}
                className="w-full min-h-[8rem] bg-white/10 border border-white/20 rounded px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-blue-500"
              />
              <div className="text-[11px] text-gray-500">
                Key/value pairs written into the generated `.mdp` files (last-write-wins).
              </div>
            </Section>
          </div>
        )}
      </div>
      <button
        type="button"
        onClick={handleSubmit}
        disabled={loading}
        className="w-full py-4 sm:py-5 text-base sm:text-lg font-black uppercase tracking-wide bg-emerald-500 hover:bg-emerald-400 disabled:bg-emerald-900 disabled:text-emerald-300/50 text-emerald-950 rounded-xl border-2 border-emerald-300 shadow-[0_0_32px_-8px_rgba(52,211,153,0.55)] transition-colors"
      >
        {loading ? "Submitting simulation…" : "Submit simulation — run MD"}
      </button>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">{title}</div>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
  min,
  max,
  step,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
}) {
  return (
    <div className="flex justify-between items-center gap-4">
      <label className="text-sm text-gray-400 shrink-0">{label}</label>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-32 bg-white/10 border border-white/20 rounded px-3 py-1.5 text-sm text-white text-right focus:outline-none focus:border-blue-500"
      />
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <div className="flex justify-between items-center gap-4">
      <label className="text-sm text-gray-400 shrink-0">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="max-w-[12rem] bg-white/10 border border-white/20 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
      >
        {options.map((o) => (
          <option key={o} value={o} className="bg-gray-900">
            {o}
          </option>
        ))}
      </select>
    </div>
  );
}

const FileInput = React.forwardRef<
  HTMLInputElement,
  { label: string; accept: string; onFileChange?: () => void }
>(({ label, accept, onFileChange }, ref) => (
  <div>
    <label className="text-sm text-gray-400 block mb-1">{label}</label>
    <input
      ref={ref}
      type="file"
      accept={accept}
      onChange={() => onFileChange?.()}
      className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border file:border-white/20 file:bg-white/5 file:text-gray-300 hover:file:bg-white/10"
    />
  </div>
));
FileInput.displayName = "FileInput";

function ToggleField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-4 text-sm text-gray-300">
      <span className="text-gray-400">{label}</span>
      <input
        type="checkbox"
        checked={value}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 accent-emerald-400"
      />
    </label>
  );
}
