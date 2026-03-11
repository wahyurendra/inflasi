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
  } catch {
    // DB not connected — return mock data
    return NextResponse.json({
      data: [
        { kodeKomoditas: "CABAI_RAWIT", namaDisplay: "Cabai Rawit", kategori: "bumbu", satuan: "kg", hargaTerakhir: 85000, perubahanHarian: 2.1, perubahanMingguan: 12.0, perubahanBulanan: 18.5 },
        { kodeKomoditas: "BAWANG_MERAH", namaDisplay: "Bawang Merah", kategori: "bumbu", satuan: "kg", hargaTerakhir: 42000, perubahanHarian: 0.5, perubahanMingguan: 7.0, perubahanBulanan: 11.2 },
        { kodeKomoditas: "TELUR_AYAM", namaDisplay: "Telur Ayam", kategori: "protein", satuan: "kg", hargaTerakhir: 28500, perubahanHarian: 0.8, perubahanMingguan: 4.0, perubahanBulanan: 6.1 },
        { kodeKomoditas: "GULA_PASIR", namaDisplay: "Gula Pasir", kategori: "minyak_gula", satuan: "kg", hargaTerakhir: 17200, perubahanHarian: 0.2, perubahanMingguan: 2.0, perubahanBulanan: 3.5 },
        { kodeKomoditas: "BERAS", namaDisplay: "Beras", kategori: "bahan_pokok", satuan: "kg", hargaTerakhir: 14850, perubahanHarian: 0.3, perubahanMingguan: 1.2, perubahanBulanan: 3.8 },
        { kodeKomoditas: "MINYAK_GORENG", namaDisplay: "Minyak Goreng", kategori: "minyak_gula", satuan: "liter", hargaTerakhir: 18100, perubahanHarian: -0.1, perubahanMingguan: 0.5, perubahanBulanan: 1.2 },
        { kodeKomoditas: "BAWANG_PUTIH", namaDisplay: "Bawang Putih", kategori: "bumbu", satuan: "kg", hargaTerakhir: 38000, perubahanHarian: 0.0, perubahanMingguan: -0.3, perubahanBulanan: 2.1 },
        { kodeKomoditas: "CABAI_MERAH", namaDisplay: "Cabai Merah", kategori: "bumbu", satuan: "kg", hargaTerakhir: 55000, perubahanHarian: -0.5, perubahanMingguan: -1.2, perubahanBulanan: 5.3 },
      ],
      source: "mock",
    });
  }
}
