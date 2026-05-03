"use client";

import { useCallback, useRef } from "react";

type Props = {
  file: File | null;
  disabled?: boolean;
  onFile: (f: File | null) => void;
};

const ACCEPT =
  ".pdf,.png,.jpg,.jpeg,.webp,.gif,.svg,.docx,.pptx,.xlsx,application/pdf,image/*";

export function UploadDropzone({ file, disabled, onFile }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      const f = e.dataTransfer.files?.[0];
      if (f) onFile(f);
    },
    [onFile],
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        e.stopPropagation();
      }}
      onDrop={onDrop}
      className="rounded-xl border border-dashed border-mineru-border bg-mineru-panel/40 p-6 text-center"
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        disabled={disabled}
        onChange={(e) => onFile(e.target.files?.[0] ?? null)}
      />
      <p className="text-sm text-mineru-muted">
        Drag and drop a document, or choose a file
      </p>
      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        className="mt-3 rounded-lg bg-mineru-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
      >
        Browse
      </button>
      {file && (
        <p className="mt-3 truncate text-sm text-slate-200" title={file.name}>
          Selected: <span className="font-mono">{file.name}</span>
        </p>
      )}
    </div>
  );
}
