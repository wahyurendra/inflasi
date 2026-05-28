import { NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET() {
  try {
    const result = await apiClient.get("/intelligence/volatility");
    return NextResponse.json(result);
  } catch (error) {
    console.error("Volatility error:", error);
    return NextResponse.json({ data: [], error: "Database error" }, { status: 500 });
  }
}
