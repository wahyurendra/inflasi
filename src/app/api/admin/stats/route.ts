import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db";

const mockStats = {
  totalUsers: 156,
  activeUsers: 142,
  totalReports: 1847,
  pendingReports: 23,
  approvedReports: 1689,
  rejectedReports: 98,
  flaggedReports: 37,
  reportsToday: 12,
  reportsThisWeek: 67,
  reportsThisMonth: 284,
  usersByRole: {
    ADMIN: 2,
    GOVERNMENT_ANALYST: 8,
    REGIONAL_OFFICER: 15,
    REPORTER: 131,
  },
};

export async function GET() {
  try {
    const session = await auth();
    if (!session?.user || session.user.role !== "ADMIN") {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const now = new Date();
    const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const startOfWeek = new Date(startOfDay);
    startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay());
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);

    const [
      totalUsers,
      activeUsers,
      totalReports,
      pendingReports,
      approvedReports,
      rejectedReports,
      flaggedReports,
      reportsToday,
      reportsThisWeek,
      reportsThisMonth,
      adminCount,
      analystCount,
      officerCount,
      reporterCount,
    ] = await Promise.all([
      prisma.user.count(),
      prisma.user.count({ where: { isActive: true } }),
      prisma.priceReport.count(),
      prisma.priceReport.count({ where: { status: "PENDING" } }),
      prisma.priceReport.count({ where: { status: "APPROVED" } }),
      prisma.priceReport.count({ where: { status: "REJECTED" } }),
      prisma.priceReport.count({ where: { status: "FLAGGED" } }),
      prisma.priceReport.count({ where: { createdAt: { gte: startOfDay } } }),
      prisma.priceReport.count({ where: { createdAt: { gte: startOfWeek } } }),
      prisma.priceReport.count({ where: { createdAt: { gte: startOfMonth } } }),
      prisma.user.count({ where: { role: "ADMIN" } }),
      prisma.user.count({ where: { role: "GOVERNMENT_ANALYST" } }),
      prisma.user.count({ where: { role: "REGIONAL_OFFICER" } }),
      prisma.user.count({ where: { role: "REPORTER" } }),
    ]);

    return NextResponse.json({
      data: {
        totalUsers,
        activeUsers,
        totalReports,
        pendingReports,
        approvedReports,
        rejectedReports,
        flaggedReports,
        reportsToday,
        reportsThisWeek,
        reportsThisMonth,
        usersByRole: {
          ADMIN: adminCount,
          GOVERNMENT_ANALYST: analystCount,
          REGIONAL_OFFICER: officerCount,
          REPORTER: reporterCount,
        },
      },
    });
  } catch {
    return NextResponse.json({ data: mockStats, source: "mock" });
  }
}
