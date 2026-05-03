"use client";

import { useCallback, useEffect, useState } from "react";

import { ConversionOptions } from "@/components/ConversionOptions";
import { JobStatusPanel } from "@/components/JobStatusPanel";
import { ResultTabs } from "@/components/ResultTabs";
import { UploadDropzone } from "@/components/UploadDropzone";
import { convertFile, fetchJob, fetchJobs, fetchResult } from "@/lib/api";
import { DEFAULT_OCR_LANGUAGE } from "@/lib/ocrLanguages";
import type { ConversionOptionsState, JobState, ResultPayload } from "@/lib/types";

const defaultOptions = (): ConversionOptionsState => ({
  backend: "pipeline",
  maxPages: "",
  ocrLanguage: DEFAULT_OCR_LANGUAGE,
  enableTableRecognition: true,
  enableFormulaRecognition: true,
  forceOcr: false,
});

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [opts, setOpts] = useState<ConversionOptionsState>(defaultOptions);
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<JobState | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<ResultPayload | null>(null);
  const [jobs, setJobs] = useState<JobState[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  const refreshJobs = useCallback(async () => {
    try {
      const j = await fetchJobs();
      setJobs(j);
      setLoadError(null);
    } catch {
      setLoadError("Could not load job list. Is the API running on port 8000?");
    }
  }, []);

  useEffect(() => {
    void refreshJobs();
  }, [refreshJobs]);

  const loadJobBundle = useCallback(async (id: string) => {
    setJobId(id);
    try {
      const j = await fetchJob(id);
      setJob(j);
      if (j.status === "succeeded") {
        try {
          const r = await fetchResult(id);
          setResult(r);
        } catch {
          setResult(null);
        }
      } else {
        setResult(null);
      }
    } catch {
      setJob(null);
      setResult(null);
    }
  }, []);

  useEffect(() => {
    if (job?.status === "succeeded" && jobId) {
      void fetchResult(jobId)
        .then(setResult)
        .catch(() => setResult(null));
    }
    if (job?.status === "failed" || job?.status === "cancelled") {
      setResult(null);
    }
  }, [job?.status, jobId]);

  useEffect(() => {
    if (job?.status === "succeeded" || job?.status === "failed") {
      void refreshJobs();
    }
  }, [job?.status, refreshJobs]);

  const onConvert = async () => {
    if (!file) return;
    setUploading(true);
    setLoadError(null);
    setResult(null);
    try {
      const res = await convertFile(file, {
        backend: opts.backend,
        maxPages: opts.maxPages,
        ocrLanguage: opts.ocrLanguage,
        enableTableRecognition: opts.enableTableRecognition,
        enableFormulaRecognition: opts.enableFormulaRecognition,
        forceOcr: opts.forceOcr,
      });
      await loadJobBundle(res.jobId);
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Conversion request failed");
    } finally {
      setUploading(false);
    }
  };

  const onRetry = () => {
    setJobId(null);
    setJob(null);
    setResult(null);
    setFile(null);
    setOpts(defaultOptions());
  };

  const onJobUpdate = useCallback((j: JobState) => {
    setJob(j);
  }, []);

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-4 py-10">
      <header className="space-y-2 text-center">
        <p className="text-xs uppercase tracking-[0.2em] text-mineru-muted">
          Local extraction
        </p>
        <h1 className="text-3xl font-semibold text-white md:text-4xl">
          MinerU Document Extraction
        </h1>
        <p className="text-sm text-mineru-muted">
          Upload PDFs, Office documents, or images. Track progress live and inspect Markdown,
          JSON, and assets.
        </p>
      </header>

      {loadError && (
        <div className="rounded-lg border border-amber-600/50 bg-amber-950/30 px-4 py-3 text-sm text-amber-100">
          {loadError}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-4">
          <UploadDropzone
            file={file}
            disabled={uploading}
            onFile={(f) => {
              setFile(f);
              setResult(null);
            }}
          />
          <ConversionOptions value={opts} onChange={setOpts} disabled={uploading} />
          <button
            type="button"
            disabled={!file || uploading}
            onClick={() => void onConvert()}
            className="w-full rounded-xl bg-mineru-accent py-3 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-40"
          >
            {uploading ? "Uploading…" : "Convert"}
          </button>
        </div>

        <div className="space-y-4">
          <JobStatusPanel
            job={job}
            jobId={jobId}
            onRetry={onRetry}
            onJobUpdate={onJobUpdate}
          />
          <ResultTabs result={result} jobId={jobId} />
        </div>
      </div>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-100">Recent jobs</h2>
          <button
            type="button"
            onClick={() => void refreshJobs()}
            className="text-sm text-mineru-accent hover:underline"
          >
            Refresh
          </button>
        </div>
        <div className="overflow-x-auto rounded-xl border border-mineru-border">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-mineru-panel text-mineru-muted">
              <tr>
                <th className="px-3 py-2 font-medium">File</th>
                <th className="px-3 py-2 font-medium">Backend</th>
                <th className="px-3 py-2 font-medium">Status</th>
                <th className="px-3 py-2 font-medium">Updated</th>
                <th className="px-3 py-2 font-medium" />
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.jobId} className="border-t border-mineru-border bg-mineru-bg/40">
                  <td className="max-w-[200px] truncate px-3 py-2 font-mono text-xs" title={j.fileName}>
                    {j.fileName}
                  </td>
                  <td className="px-3 py-2 text-xs">{j.backend}</td>
                  <td className="px-3 py-2 capitalize">{j.status}</td>
                  <td className="px-3 py-2 text-xs text-mineru-muted">
                    {new Date(j.updatedAt).toLocaleString()}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <button
                      type="button"
                      className="text-mineru-accent hover:underline"
                      onClick={() => void loadJobBundle(j.jobId)}
                    >
                      Open
                    </button>
                  </td>
                </tr>
              ))}
              {!jobs.length && (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-mineru-muted">
                    No jobs yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
