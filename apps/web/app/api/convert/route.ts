import { NextRequest, NextResponse } from "next/server";

import { API_BASE } from "@/lib/config";

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const upstream = await fetch(`${API_BASE}/api/convert`, {
    method: "POST",
    body: formData,
  });
  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") || "application/json" },
  });
}
