import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const sort = searchParams.get("sort") || "weekly_change";
  const limit = parseInt(searchParams.get("limit") || "8");

  try {
    // Get all commodities with their latest price data
    const commodities = await prisma.dimCommodity.findMany({
      where: { isMvp: true },
      include: {
        priceDaily: {
          orderBy: { tanggal: "desc" },
          take: 1,
        },
      },
    });

    const ranking = commodities
      .map((c) => {
        const latest = c.priceDaily[0];
        return {
          kodeKomoditas: c.kodeKomoditas,
          namaDisplay: c.namaDisplay,
          kategori: c.kategori,
          satuan: c.satuan,
          hargaTerakhir: latest ? Number(latest.harga) : null,
          perubahanHarian: latest?.perubahanHarian ? Number(latest.perubahanHarian) : null,
          perubahanMingguan: latest?.perubahanMingguan ? Number(latest.perubahanMingguan) : null,
          perubahanBulanan: latest?.perubahanBulanan ? Number(latest.perubahanBulanan) : null,
        };
      })
      .sort((a, b) => {
        const key =
          sort === "daily_change"
            ? "perubahanHarian"
            : sort === "monthly_change"
              ? "perubahanBulanan"
              : "perubahanMingguan";
        return (b[key] ?? 0) - (a[key] ?? 0);
      })
      .slice(0, limit);

    return NextResponse.json({ data: ranking });
  } catch (error) {
    console.error("Commodity ranking error:", error);
    return NextResponse.json({ data: [], error: "Database error" }, { status: 500 });
  }
}
