/**
 * Simulate flow: download the server-generated bootstrap script so Docker / GROMACS
 * worker dependencies can be installed locally (`CALY360_ROOT` + `docker compose`).
 * DYNAMICS UI is code-split via the `/dynamics` route lazy chunk in `App.tsx`.
 */
import { apiClient } from "../api/client";

export async function downloadLocalBootstrapScript(): Promise<void> {
  const base = (apiClient.defaults.baseURL || "").replace(/\/$/, "");
  const url = `${base}/dynamics/local-bootstrap.sh`;
  const res = await fetch(url, { method: "GET" });
  if (!res.ok) {
    throw new Error(`Bootstrap script HTTP ${res.status}`);
  }
  const blob = await res.blob();
  const href = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = href;
  a.download = "caly360-dynamics-local-setup.sh";
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(href);
}

export async function prepareSimulateEnvironment(): Promise<void> {
  await downloadLocalBootstrapScript();
}
