import { Download } from "lucide-react";
import { getDownloadUrl } from "../../api/dynamics";

export default function OutputDownloader({ jobId }: { jobId: string }) {
  if (!jobId) return null;
  const url = getDownloadUrl(jobId);
  return (
    <a
      href={url}
      className="flex items-center justify-center gap-2 rounded-xl border border-white/[0.1] bg-white/[0.04] px-4 py-3 text-sm font-semibold text-caly-mist hover:border-violet-400/30 hover:bg-violet-500/[0.08] transition-colors"
    >
      <Download className="h-4 w-4 text-violet-300/80" strokeWidth={1.5} />
      Download outputs (ZIP)
    </a>
  );
}
