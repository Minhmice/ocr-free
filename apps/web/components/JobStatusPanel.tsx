"use client";

import { useEffect, useRef, useState } from "react";

import type { JobState } from "@/lib/types";

type Props = {
  job: JobState | null;
  jobId: string | null;
  onRetry: () => void;
  onJobUpdate?: (j: JobState) => void;
};

type LogTab = "all" | "stdout" | "stderr";

export function JobStatusPanel({ job, jobId, onRetry, onJobUpdate }: Props) {
  const [logTab, setLogTab] = useState<LogTab>("all");
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
  }, [
    job?.stdoutTail,
    job?.stderrTail,
    job?.progressMessage,
    job?.status,
    logTab,
  ]);

  if (!job && !jobId) {
    return (
      <div className="flex flex-col gap-4">
        <div className="rounded-xl border border-mineru-border bg-mineru-panel p-4 text-sm text-mineru-muted">
          Run a conversion to see live status and MinerU logs.
        </div>
        <div className="rounded-xl border border-dashed border-mineru-border bg-[#0a0f1a]/80 p-4 font-mono text-xs text-mineru-muted">
          <p className="mb-2 font-sans text-[11px] uppercase tracking-wide">
            Conversion log
          </p>
          Log output from <code className="text-slate-400">mineru</code> will appear here
          (stdout / stderr), similar to Gradio’s conversion panel.
        </div>
      </div>
    );
  }

  const status = job?.status ?? "queued";
  const out = job?.stdoutTail ?? [];
  const err = job?.stderrTail ?? [];
  const outLines = out.length;
  const errLines = err.length;

  const stdoutBlock = out.join("\n") || "— (no stdout yet)";
  const stderrBlock = err.join("\n") || "— (no stderr yet)";
  const combinedBlock = [
    "──────────────────────────────── stdout ────────────────────────────────",
    stdoutBlock,
    "",
    "──────────────────────────────── stderr ────────────────────────────────",
    stderrBlock,
  ].join("\n");

  let logBody: string;
  if (logTab === "stdout") logBody = stdoutBlock;
  else if (logTab === "stderr") logBody = stderrBlock;
  else logBody = combinedBlock;

  const logAccent =
    logTab === "stderr"
      ? "text-amber-200/95"
      : logTab === "stdout"
        ? "text-slate-200"
        : "text-slate-200";

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      {/* Compact conversion status (Gradio-style header strip) */}
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

        {job?.error && status === "failed" && (
          <pre className="mt-3 max-h-36 overflow-auto rounded-lg bg-red-950/50 p-3 font-mono text-xs text-red-200">
            {job.error}
          </pre>
        )}
      </div>

      {/* Large live terminal — primary debugging surface */}
      <div className="flex min-h-[min(50vh,480px)] flex-1 flex-col overflow-hidden rounded-xl border border-mineru-border bg-[#070b14] shadow-inner">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-mineru-border bg-mineru-panel/95 px-3 py-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-mineru-muted">
            Live log <span className="font-normal text-slate-500">(mineru)</span>
          </span>
          <div className="flex flex-wrap gap-1">
            {(
              [
                ["all", `All (${outLines + errLines} lines)`],
                ["stdout", `stdout (${outLines})`],
                ["stderr", `stderr (${errLines})`],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                onClick={() => setLogTab(id)}
                className={`rounded-md px-2.5 py-1 text-[11px] font-medium ${
                  logTab === id
                    ? "bg-mineru-accent text-white"
                    : "bg-black/30 text-mineru-muted hover:bg-white/10 hover:text-slate-200"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div
          ref={logScrollRef}
          className="min-h-[280px] flex-1 overflow-auto overscroll-contain px-3 py-3"
        >
          <pre
            className={`whitespace-pre-wrap break-all font-mono text-[11px] leading-relaxed ${logAccent}`}
          >
            {logBody}
          </pre>
        </div>

        <p className="border-t border-mineru-border px-3 py-2 font-mono text-[10px] text-mineru-muted">
          Tip: if stdout/stderr stay empty while status is running, confirm{" "}
          <code className="text-slate-500">mineru</code> is installed in the API venv and check the
          API terminal.
        </p>
      </div>
    </div>
  );
}
