import { NextResponse } from "next/server";

import { API_BASE } from "@/lib/config";

type Ctx = { params: { jobId: string } };

export async function GET(_req: Request, { params }: Ctx) {
  const upstream = await fetch(`${API_BASE}/api/jobs/${params.jobId}/events`, {
    cache: "no-store",
    headers: { Accept: "text/event-stream" },
  });

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
