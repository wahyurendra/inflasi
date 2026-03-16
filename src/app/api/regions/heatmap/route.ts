import { NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET() {
  try {
    const result = await apiClient.get<{ data: unknown[] }>("/regions/heatmap");
    return NextResponse.json(result);
  } catch {
    return NextResponse.json({ data: [], source: "mock" });
  }
}
