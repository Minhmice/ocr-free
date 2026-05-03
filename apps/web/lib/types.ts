import type { OcrLanguageCode } from "./ocrLanguages";

export type BackendName = "pipeline" | "vlm-auto-engine" | "hybrid-auto-engine";

export type JobStatus = "queued" | "running" | "succeeded" | "failed" | "cancelled";

export interface JobState {
  jobId: string;
  fileName: string;
  status: JobStatus;
  backend: string;
  createdAt: string;
  updatedAt: string;
  progressMessage: string;
  stdoutTail: string[];
  stderrTail: string[];
  error: string | null;
}

export interface ConvertResponse {
  jobId: string;
  status: "queued";
}

export interface ConversionOptionsState {
  backend: BackendName;
  maxPages: string;
  ocrLanguage: OcrLanguageCode;
  enableTableRecognition: boolean;
  enableFormulaRecognition: boolean;
  forceOcr: boolean;
}

export interface AssetRef {
  path: string;
  url: string;
}

export interface ResultPayload {
  markdown: string;
  markdownPlain: string;
  json: unknown;
  assets: AssetRef[];
  downloadUrl: string;
}
