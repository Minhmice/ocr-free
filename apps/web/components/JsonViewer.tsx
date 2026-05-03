"use client";

type Props = {
  data: unknown;
};

export function JsonViewer({ data }: Props) {
  const text =
    data === undefined || data === null
      ? ""
      : typeof data === "string"
        ? data
        : JSON.stringify(data, null, 2);

  return (
    <pre className="max-h-[480px] overflow-auto rounded-lg bg-black/40 p-4 text-xs text-emerald-100/90">
      {text || "—"}
    </pre>
  );
}
