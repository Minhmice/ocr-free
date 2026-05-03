import { NextResponse } from "next/server";

import { API_BASE } from "@/lib/config";

type Ctx = { params: { jobId: string } };

export async function GET(_req: Request, { params }: Ctx) {
  const upstream = await fetch(`${API_BASE}/api/jobs/${params.jobId}`, {
    cache: "no-store",
  });
  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: { "Content-Type": "application/json" },
  });
}
