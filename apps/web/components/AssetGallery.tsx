"use client";

import type { AssetRef } from "@/lib/types";

type Props = {
  assets: AssetRef[];
};

export function AssetGallery({ assets }: Props) {
  if (!assets.length) {
    return <p className="text-sm text-mineru-muted">No image assets found.</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {assets.map((a) => (
        <div
          key={a.path}
          className="overflow-hidden rounded-lg border border-mineru-border bg-mineru-bg/60"
        >
          <div className="flex h-48 w-full items-center justify-center bg-black/20 p-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={a.url}
              alt={a.path}
              className="max-h-full max-w-full object-contain"
            />
          </div>
          <p className="truncate px-2 py-1 font-mono text-xs text-mineru-muted" title={a.path}>
            {a.path}
          </p>
        </div>
      ))}
    </div>
  );
}
