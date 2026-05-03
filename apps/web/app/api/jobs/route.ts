import { NextResponse } from "next/server";

import { API_BASE } from "@/lib/config";

export async function GET() {
  const upstream = await fetch(`${API_BASE}/api/jobs`, { cache: "no-store" });
  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: { "Content-Type": "application/json" },
  });
}
