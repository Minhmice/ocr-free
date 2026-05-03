"use client";

import { useEffect, useState } from "react";

import type { JobState } from "@/lib/types";

type Props = {
  job: JobState | null;
  jobId: string | null;
  onRetry: () => void;
  onJobUpdate?: (j: JobState) => void;
};

export function JobStatusPanel({ job, jobId, onRetry, onJobUpdate }: Props) {
  const [openOut, setOpenOut] = useState(false);
  const [openErr, setOpenErr] = useState(true);

  useEffect(() => {
    if (!jobId) return;
    const es = new EventSource(`/api/jobs/${jobId}/events`);
    es.addEventListener("job", (ev) => {
      try {
        const data = JSON.parse((ev as MessageEvent).data) as JobState;
        if (!data?.jobId) return;
        onJobUpdate?.(data);
      } catch {
        /* ignore */
      }
    });
    es.onerror = () => {
      es.close();
    };
    return () => es.close();
  }, [jobId]);

  if (!job && !jobId) {
    return (
      <div className="rounded-xl border border-mineru-border bg-mineru-panel p-4 text-sm text-mineru-muted">
        Run a conversion to see live status.
      </div>
    );
  }

  const status = job?.status ?? "queued";

  return (
    <div className="space-y-3 rounded-xl border border-mineru-border bg-mineru-panel p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs uppercase tracking-wide text-mineru-muted">Status</p>
          <p className="text-lg font-semibold capitalize text-slate-100">{status}</p>
        </div>
        <button
          type="button"
          onClick={onRetry}
          className="rounded-lg border border-mineru-border px-3 py-1.5 text-sm hover:bg-white/5"
        >
          Retry
        </button>
      </div>

      {job?.progressMessage && (
        <p className="text-sm text-slate-300">{job.progressMessage}</p>
      )}

      {job?.error && status === "failed" && (
        <pre className="max-h-40 overflow-auto rounded-lg bg-red-950/40 p-3 text-xs text-red-200">
          {job.error}
        </pre>
      )}

      <div>
        <button
          type="button"
          className="text-xs text-mineru-accent"
          onClick={() => setOpenOut((o) => !o)}
        >
          {openOut ? "Hide" : "Show"} stdout ({job?.stdoutTail?.length ?? 0} lines)
        </button>
        {openOut && (
          <pre className="mt-2 max-h-48 overflow-auto rounded-lg bg-black/30 p-2 text-xs text-slate-300">
            {(job?.stdoutTail ?? []).join("\n") || "—"}
          </pre>
        )}
      </div>

      <div>
        <button
          type="button"
          className="text-xs text-mineru-accent"
          onClick={() => setOpenErr((o) => !o)}
        >
          {openErr ? "Hide" : "Show"} stderr ({job?.stderrTail?.length ?? 0} lines)
        </button>
        {openErr && (
          <pre className="mt-2 max-h-48 overflow-auto rounded-lg bg-black/30 p-2 text-xs text-amber-200/90">
            {(job?.stderrTail ?? []).join("\n") || "—"}
          </pre>
        )}
      </div>
    </div>
  );
}
