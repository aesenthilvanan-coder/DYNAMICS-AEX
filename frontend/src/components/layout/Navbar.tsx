import { Link } from "react-router-dom";
import { Download, Orbit, PlaySquare } from "lucide-react";
import BackendStatus from "./BackendStatus";

export default function Navbar() {
  return (
    <header className="border-b border-white/[0.06] bg-caly-matte/80 backdrop-blur-md shrink-0">
      <div className="h-12 px-4 flex items-center justify-between gap-4">
        <Link to="/dynamics" className="font-mono text-sm font-semibold tracking-tight text-caly-mist shrink-0 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-gradient-to-br from-spectral-rose via-spectral-cyan to-spectral-violet opacity-90" />
          Caly360 DYNAMICS
        </Link>
        <nav className="hidden md:flex items-center gap-1 shrink-0">
          <a
            href="#install"
            className="px-3 py-2 rounded-md text-xs font-semibold uppercase tracking-wider transition-colors text-caly-dim hover:text-caly-mist hover:bg-white/[0.06] inline-flex items-center gap-1"
          >
            <Download className="h-3 w-3" strokeWidth={1.5} />
            Installer
          </a>
          <a
            href="#submit"
            className="px-3 py-2 rounded-md text-xs font-semibold uppercase tracking-wider transition-colors text-caly-dim hover:text-caly-mist hover:bg-white/[0.06] inline-flex items-center gap-1"
          >
            <PlaySquare className="h-3 w-3" strokeWidth={1.5} />
            Submit
          </a>
          <a
            href="#aex"
            className="px-3 py-2 rounded-md text-xs font-semibold uppercase tracking-wider transition-colors text-caly-dim hover:text-caly-mist hover:bg-white/[0.06] inline-flex items-center gap-1"
          >
            <Orbit className="h-3 w-3" strokeWidth={1.5} />
            AEX
          </a>
        </nav>
        <BackendStatus />
      </div>
    </header>
  );
}
