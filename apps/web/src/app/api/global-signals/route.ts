import { NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET() {
  try {
    const result = await apiClient.get("/global-signals/");

    return NextResponse.json(result);
  } catch (error) {
    console.error("Global signals error:", error);
    return NextResponse.json({ error: "Database error" }, { status: 500 });
  }
}
