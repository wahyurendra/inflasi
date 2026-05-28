import { NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET() {
  try {
    const data = await apiClient.get("/reports/stats");
    return NextResponse.json(data);
  } catch (error) {
    console.error("Report stats error:", error);
    return NextResponse.json({
      total: 0, approved: 0, pending: 0, flagged: 0, rejected: 0, approvalRate: 0,
      error: "Database error",
    }, { status: 500 });
  }
}
