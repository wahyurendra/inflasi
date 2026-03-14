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
  } catch (error) {
    console.error("Report stats error:", error);
    return NextResponse.json({
      total: 0, approved: 0, pending: 0, flagged: 0, rejected: 0, approvalRate: 0,
      error: "Database error",
    }, { status: 500 });
  }
}
