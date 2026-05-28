import { NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET(request: Request) {
  const authToken = request.headers.get("authorization") ?? undefined;
  if (!authToken) {
    return NextResponse.json({ count: 0 });
  }

  try {
    const opts = { authToken };
    const data = await apiClient.get<{ count: number }>("/notifications/count", undefined, opts);
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ count: 0 });
  }
}
