import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

const mockLeaderboard = [
  { rank: 1, name: "Siti Aminah", points: 850, reports: 72, badges: 5, province: "DKI Jakarta" },
  { rank: 2, name: "Budi Santoso", points: 720, reports: 61, badges: 4, province: "Jawa Barat" },
  { rank: 3, name: "Dewi Lestari", points: 680, reports: 55, badges: 4, province: "Jawa Tengah" },
  { rank: 4, name: "Ahmad Rizki", points: 540, reports: 43, badges: 3, province: "Jawa Timur" },
  { rank: 5, name: "Putri Wulandari", points: 490, reports: 38, badges: 3, province: "DKI Jakarta" },
  { rank: 6, name: "Eko Prasetyo", points: 420, reports: 33, badges: 2, province: "Banten" },
  { rank: 7, name: "Rina Marlina", points: 380, reports: 28, badges: 2, province: "Jawa Barat" },
  { rank: 8, name: "Hendra Wijaya", points: 350, reports: 26, badges: 2, province: "Sumatera Utara" },
  { rank: 9, name: "Fitri Handayani", points: 320, reports: 24, badges: 1, province: "Sulawesi Selatan" },
  { rank: 10, name: "Yusuf Ibrahim", points: 290, reports: 21, badges: 1, province: "Kalimantan Timur" },
];

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
  } catch {
    return NextResponse.json({ data: mockLeaderboard, source: "mock" });
  }
}
