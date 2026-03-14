import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const period = searchParams.get("period") || "all";
  const limit = parseInt(searchParams.get("limit") || "20");

  try {
    const orderBy = period === "month" ? "monthlyPoints" : "totalPoints";

    const leaders = await prisma.userPoints.findMany({
      orderBy: { [orderBy]: "desc" },
      take: limit,
      include: {
        user: {
          select: {
            name: true,
            region: { select: { namaProvinsi: true } },
            badges: { select: { badge: { select: { name: true, icon: true } } } },
          },
        },
      },
    });

    const data = leaders.map((l, i) => ({
      rank: i + 1,
      name: l.user.name || "Anonim",
      points: period === "month" ? l.monthlyPoints : l.totalPoints,
      reports: l.approvedReports,
      streak: l.currentStreak,
      badges: l.user.badges.length,
      province: l.user.region?.namaProvinsi || "-",
    }));

    return NextResponse.json({ data });
  } catch (error) {
    console.error("Leaderboard error:", error);
    return NextResponse.json({ data: [], error: "Database error" }, { status: 500 });
  }
}
