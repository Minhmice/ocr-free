"use client";

import type { ConversionOptionsState } from "@/lib/types";

type Props = {
  value: ConversionOptionsState;
  onChange: (v: ConversionOptionsState) => void;
  disabled?: boolean;
};

export function ConversionOptions({ value, onChange, disabled }: Props) {
  const set = (patch: Partial<ConversionOptionsState>) =>
    onChange({ ...value, ...patch });

  return (
    <div className="space-y-4 rounded-xl border border-mineru-border bg-mineru-panel p-4">
      <h3 className="text-sm font-semibold text-slate-100">Options</h3>

      <label className="block text-xs text-mineru-muted">
        Backend
        <select
          disabled={disabled}
          className="mt-1 w-full rounded-lg border border-mineru-border bg-mineru-bg px-3 py-2 text-sm"
          value={value.backend}
          onChange={(e) =>
            set({ backend: e.target.value as ConversionOptionsState["backend"] })
          }
        >
          <option value="pipeline">pipeline (CPU-friendly)</option>
          <option value="vlm-auto-engine">vlm-auto-engine</option>
          <option value="hybrid-auto-engine">hybrid-auto-engine</option>
        </select>
      </label>

      <label className="block text-xs text-mineru-muted">
        Max pages (empty = unlimited)
        <input
          disabled={disabled}
          type="text"
          inputMode="numeric"
          placeholder="e.g. 10"
          className="mt-1 w-full rounded-lg border border-mineru-border bg-mineru-bg px-3 py-2 text-sm"
          value={value.maxPages}
          onChange={(e) => set({ maxPages: e.target.value })}
        />
      </label>

      <label className="block text-xs text-mineru-muted">
        OCR language
        <input
          disabled={disabled}
          type="text"
          className="mt-1 w-full rounded-lg border border-mineru-border bg-mineru-bg px-3 py-2 text-sm"
          value={value.ocrLanguage}
          onChange={(e) => set({ ocrLanguage: e.target.value })}
        />
      </label>

      <div className="flex flex-col gap-2 text-sm">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            disabled={disabled}
            checked={value.enableTableRecognition}
            onChange={(e) => set({ enableTableRecognition: e.target.checked })}
          />
          Enable table recognition
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            disabled={disabled}
            checked={value.enableFormulaRecognition}
            onChange={(e) => set({ enableFormulaRecognition: e.target.checked })}
          />
          Enable formula recognition
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            disabled={disabled}
            checked={value.forceOcr}
            onChange={(e) => set({ forceOcr: e.target.checked })}
          />
          Force OCR
        </label>
      </div>
    </div>
  );
}
