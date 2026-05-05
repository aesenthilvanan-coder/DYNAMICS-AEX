import { NavLink } from "react-router-dom";
import { Download, FlaskConical, Home, Orbit, PlaySquare } from "lucide-react";

const linkBase =
  "flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-colors";

function item({ isActive }: { isActive: boolean }) {
  return [
    linkBase,
    isActive ? "bg-white/[0.08] text-caly-mist shadow-spectral-inset" : "text-caly-dim hover:text-caly-mist hover:bg-white/[0.04]",
  ].join(" ");
}

export default function Sidebar() {
  return (
    <aside className="w-56 shrink-0 border-r border-white/[0.06] bg-caly-matte/95 hidden md:flex flex-col">
      <NavLink
        to="/dynamics"
        end
        className="h-12 px-4 flex items-center gap-2 border-b border-white/[0.06] text-sm font-semibold tracking-tight hover:bg-white/[0.03]"
      >
        <Home className="h-4 w-4 text-caly-dim" strokeWidth={1.5} />
        DYNAMICS
      </NavLink>
      <div className="p-3 space-y-1">
        <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-caly-dim px-2 mb-1">
          Navigate
        </div>
        <NavLink to="/dynamics" className={item}>
          <Orbit className="h-3.5 w-3.5 opacity-80" strokeWidth={1.5} />
          DYNAMICS
        </NavLink>
        <a href="#install" className={linkBase + " text-caly-dim hover:text-caly-mist hover:bg-white/[0.04]"}>
          <Download className="h-3.5 w-3.5 opacity-80" strokeWidth={1.5} />
          Installer
        </a>
        <a href="#aex" className={linkBase + " text-caly-dim hover:text-caly-mist hover:bg-white/[0.04]"}>
          <FlaskConical className="h-3.5 w-3.5 opacity-80" strokeWidth={1.5} />
          AEX Math
        </a>
        <a href="#submit" className={linkBase + " text-caly-dim hover:text-caly-mist hover:bg-white/[0.04]"}>
          <PlaySquare className="h-3.5 w-3.5 opacity-80" strokeWidth={1.5} />
          Submit Job
        </a>
      </div>
      <div className="flex-1 min-h-0 flex flex-col p-3 border-t border-white/[0.06]">
        <p className="text-[10px] text-caly-dim px-2 leading-relaxed">
          Download the installer, bring up the GROMACS stack, then submit MD jobs from the same page.
        </p>
      </div>
    </aside>
  );
}
