import { NextResponse } from "next/server";

import { API_BASE } from "@/lib/config";

type Ctx = { params: { jobId: string; path: string[] } };

export async function GET(_req: Request, { params }: Ctx) {
  const rel = params.path.map(encodeURIComponent).join("/");
  const upstream = await fetch(
    `${API_BASE}/api/jobs/${params.jobId}/assets/${rel}`,
    { cache: "no-store" },
  );

  const headers = new Headers();
  const ct = upstream.headers.get("content-type");
  if (ct) headers.set("Content-Type", ct);

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers,
  });
}
