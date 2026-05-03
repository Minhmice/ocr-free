import { NextResponse } from "next/server";

import { API_BASE } from "@/lib/config";

type Ctx = { params: { jobId: string } };

export async function GET(_req: Request, { params }: Ctx) {
  const upstream = await fetch(`${API_BASE}/api/jobs/${params.jobId}/download`, {
    cache: "no-store",
  });

  const headers = new Headers();
  const ct = upstream.headers.get("content-type");
  const cd = upstream.headers.get("content-disposition");
  if (ct) headers.set("Content-Type", ct);
  if (cd) headers.set("Content-Disposition", cd);

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers,
  });
}
