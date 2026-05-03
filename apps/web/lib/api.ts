import type { ConvertResponse, JobState, ResultPayload } from "./types";

/** Browser calls same-origin Next routes; route handlers proxy to FastAPI. */

export async function convertFile(
  file: File,
  form: Record<string, string | boolean>,
): Promise<ConvertResponse> {
  const body = new FormData();
  body.append("file", file);
  body.append("backend", String(form.backend));
  body.append("maxPages", String(form.maxPages ?? ""));
  body.append("ocrLanguage", String(form.ocrLanguage));
  body.append("enableTableRecognition", String(form.enableTableRecognition));
  body.append("enableFormulaRecognition", String(form.enableFormulaRecognition));
  body.append("forceOcr", String(form.forceOcr));

  const res = await fetch("/api/convert", {
    method: "POST",
    body,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as {
      detail?: { error?: { message?: string } } | string;
      error?: { message?: string };
    };
    const fromDetail =
      typeof err.detail === "object" && err.detail?.error?.message
        ? err.detail.error.message
        : null;
    const fromTop = err.error?.message;
    throw new Error(
      fromDetail ?? fromTop ?? `Convert failed (${res.status})`,
    );
  }
  return res.json() as Promise<ConvertResponse>;
}

export async function fetchJobs(): Promise<JobState[]> {
  const res = await fetch("/api/jobs", { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load jobs");
  return res.json() as Promise<JobState[]>;
}

export async function fetchJob(jobId: string): Promise<JobState> {
  const res = await fetch(`/api/jobs/${jobId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Job not found");
  return res.json() as Promise<JobState>;
}

export async function fetchResult(jobId: string): Promise<ResultPayload> {
  const res = await fetch(`/api/jobs/${jobId}/result`, { cache: "no-store" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      (err as { error?: { message?: string } })?.error?.message ?? "Result not ready",
    );
  }
  return res.json() as Promise<ResultPayload>;
}
