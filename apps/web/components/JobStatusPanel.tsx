"use client";

import { useEffect, useRef } from "react";

import type { JobState } from "@/lib/types";

type Props = {
  job: JobState | null;
  jobId: string | null;
  onRetry: () => void;
  onJobUpdate?: (j: JobState) => void;
};

/** Single combined view: API/server messages + MinerU stdout + stderr (no separate tabs). */
function buildUnifiedLog(job: JobState | null): string {
  if (!job) return "";
  const chunks: string[] = [];
  if (job.error?.trim()) {
    chunks.push(job.error.trim());
  }
  const out = job.stdoutTail ?? [];
  const err = job.stderrTail ?? [];
  const stream = [...out, ...err].join("\n").trim();
  if (stream) {
    chunks.push(stream);
  }
  if (!chunks.length) {
    return "(no log lines yet — if this stays empty, check that `mineru` is installed for the API process.)";
  }
  return chunks.join("\n\n");
}

export function JobStatusPanel({ job, jobId, onRetry, onJobUpdate }: Props) {
  const logScrollRef = useRef<HTMLDivElement>(null);

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
  }, [jobId, onJobUpdate]);

  useEffect(() => {
    const el = logScrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [job?.stdoutTail, job?.stderrTail, job?.progressMessage, job?.status, job?.error]);

  if (!job && !jobId) {
    return (
      <div className="flex flex-col gap-4">
        <div className="rounded-xl border border-mineru-border bg-mineru-panel p-4 text-sm text-mineru-muted">
          Run a conversion to see live status and MinerU logs.
        </div>
        <div className="rounded-xl border border-dashed border-mineru-border bg-[#0a0f1a]/80 p-4 font-mono text-xs text-mineru-muted">
          <p className="mb-2 font-sans text-[11px] uppercase tracking-wide">Live log</p>
          All MinerU output and errors appear in one scrollable panel below status.
        </div>
      </div>
    );
  }

  const status = job?.status ?? "queued";
  const unifiedLog = buildUnifiedLog(job);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <div className="rounded-xl border border-mineru-border bg-mineru-panel p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-1">
            <p className="text-xs uppercase tracking-wide text-mineru-muted">
              Conversion status
            </p>
            <p className="text-xl font-semibold capitalize tracking-tight text-slate-100">
              {status}
            </p>
            {job?.progressMessage ? (
              <p className="max-w-prose text-sm text-slate-400">{job.progressMessage}</p>
            ) : (
              <p className="text-sm text-mineru-muted">
                {status === "running"
                  ? "MinerU is running… watch the log below."
                  : status === "queued"
                    ? "Waiting to start…"
                    : null}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onRetry}
            className="shrink-0 rounded-lg border border-mineru-border px-3 py-1.5 text-sm hover:bg-white/5"
          >
            Retry
          </button>
        </div>
      </div>

      <div className="flex min-h-[min(50vh,480px)] flex-1 flex-col overflow-hidden rounded-xl border border-mineru-border bg-[#070b14] shadow-inner">
        <div className="border-b border-mineru-border bg-mineru-panel/95 px-3 py-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-mineru-muted">
            Live log
          </span>
        </div>

        <div
          ref={logScrollRef}
          className="min-h-[280px] flex-1 overflow-auto overscroll-contain px-3 py-3"
        >
          <pre className="whitespace-pre-wrap break-all font-mono text-[11px] leading-relaxed text-slate-200">
            {unifiedLog}
          </pre>
        </div>
      </div>
    </div>
  );
}
