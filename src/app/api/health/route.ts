import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET() {
  const health: Record<string, unknown> = {
    status: "ok",
    timestamp: new Date().toISOString(),
    version: "0.2.0",
  };

  // Check database
  try {
    const regionCount = await prisma.dimRegion.count();
    const latestPrice = await prisma.factPriceDaily.findFirst({
      orderBy: { tanggal: "desc" },
      select: { tanggal: true },
    });
    const activeAlerts = await prisma.analyticsAlert.count({
      where: { isActive: true },
    });

    health.database = {
      connected: true,
      regions: regionCount,
      latestPriceDate: latestPrice?.tanggal?.toISOString().slice(0, 10) || null,
      activeAlerts,
    };
  } catch {
    health.database = { connected: false };
    health.status = "degraded";
  }

  // Check analytics service
  try {
    const analyticsUrl = process.env.ANALYTICS_API_URL || "http://localhost:8000";
    const resp = await fetch(`${analyticsUrl}/health`, {
      signal: AbortSignal.timeout(3000),
    });
    health.analytics = { connected: resp.ok };
  } catch {
    health.analytics = { connected: false };
  }

  const statusCode = health.status === "ok" ? 200 : 503;
  return NextResponse.json(health, { status: statusCode });
}
