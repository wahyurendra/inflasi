import { NextResponse } from "next/server";
import { apiClient } from "@/lib/api-client";

export async function GET() {
  const health: Record<string, unknown> = {
    status: "ok",
    timestamp: new Date().toISOString(),
    version: "0.2.0",
  };

  // Check database via FastAPI backend
  try {
    const dbStats = await apiClient.get("/health/db-stats");
    health.database = {
      connected: true,
      ...dbStats as Record<string, unknown>,
    };
  } catch {
    health.database = { connected: false };
    health.status = "degraded";
  }

  // Check analytics service via FastAPI root health (at /health, not /api/health)
  try {
    const analyticsUrl = process.env.ANALYTICS_API_URL || "http://localhost:8002";
    const resp = await fetch(`${analyticsUrl}/health`, {
      signal: AbortSignal.timeout(5_000),
    });
    health.analytics = { connected: resp.ok };
  } catch {
    health.analytics = { connected: false };
  }

  const statusCode = health.status === "ok" ? 200 : 503;
  return NextResponse.json(health, { status: statusCode });
}
