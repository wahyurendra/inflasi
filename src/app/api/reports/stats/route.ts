import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET() {
  try {
    const [total, approved, pending, flagged] = await Promise.all([
      prisma.priceReport.count(),
      prisma.priceReport.count({ where: { status: "APPROVED" } }),
      prisma.priceReport.count({ where: { status: "PENDING" } }),
      prisma.priceReport.count({ where: { status: "FLAGGED" } }),
    ]);

    return NextResponse.json({
      total,
      approved,
      pending,
      flagged,
      rejected: total - approved - pending - flagged,
      approvalRate: total > 0 ? Math.round((approved / total) * 100) : 0,
    });
  } catch {
    return NextResponse.json({
      total: 127,
      approved: 98,
      pending: 15,
      flagged: 5,
      rejected: 9,
      approvalRate: 77,
      source: "mock",
    });
  }
}
