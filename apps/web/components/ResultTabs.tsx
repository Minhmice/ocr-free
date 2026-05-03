"use client";

import { useMemo, useState } from "react";

import type { ResultPayload } from "@/lib/types";

import { AssetGallery } from "./AssetGallery";
import { JsonViewer } from "./JsonViewer";
import { MarkdownPreview } from "./MarkdownPreview";

type Props = {
  result: ResultPayload | null;
  jobId: string | null;
};

const tabs = ["Preview", "Markdown", "JSON", "Assets"] as const;

export function ResultTabs({ result, jobId }: Props) {
  const [tab, setTab] = useState<(typeof tabs)[number]>("Preview");

  const downloadHref = useMemo(() => {
    if (result?.downloadUrl) return result.downloadUrl;
    if (!jobId) return "#";
    return `/api/jobs/${jobId}/download`;
  }, [jobId, result?.downloadUrl]);

  if (!result) {
    return (
      <div className="rounded-xl border border-mineru-border bg-mineru-panel p-4 text-sm text-mineru-muted">
        Results appear when the job succeeds.
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-xl border border-mineru-border bg-mineru-panel p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex gap-1">
          {tabs.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={`rounded-lg px-3 py-1.5 text-sm ${
                tab === t
                  ? "bg-mineru-accent text-white"
                  : "text-mineru-muted hover:bg-white/5"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <a
          href={downloadHref}
          className="rounded-lg border border-mineru-border px-3 py-1.5 text-sm hover:bg-white/5"
        >
          Download ZIP
        </a>
      </div>

      {tab === "Preview" && <MarkdownPreview markdown={result.markdown} />}

      {tab === "Markdown" && (
        <pre className="max-h-[480px] overflow-auto whitespace-pre-wrap rounded-lg bg-black/30 p-3 text-sm text-slate-200">
          {result.markdownPlain || "—"}
        </pre>
      )}

      {tab === "JSON" && <JsonViewer data={result.json} />}

      {tab === "Assets" && <AssetGallery assets={result.assets} />}
    </div>
  );
}
