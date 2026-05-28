import { NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET() {
  try {
    const result = await apiClient.get("/recommendations/");
    return NextResponse.json({ recommendations: result });
  } catch (error) {
    console.error("Recommendations error:", error);
    return NextResponse.json({
      recommendations: [],
      error: "Analytics service error",
    }, { status: 503 });
  }
}
