import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const commodity = searchParams.get("commodity");
  const region = searchParams.get("region") || "00";
  const days = parseInt(searchParams.get("days") || "30");

  if (!commodity) {
    return NextResponse.json({ error: "commodity parameter required" }, { status: 400 });
  }

  try {
    const since = new Date();
    since.setDate(since.getDate() - days);

    const prices = await prisma.factPriceDaily.findMany({
      where: {
        commodity: { kodeKomoditas: commodity },
        region: { kodeWilayah: region },
        tanggal: { gte: since },
      },
      include: { commodity: true, region: true },
      orderBy: { tanggal: "asc" },
    });

    if (!prices.length) {
      return NextResponse.json({
        commodity: null,
        region: null,
        data: [],
        summary: null,
      });
    }

    const hargaList = prices.map((p) => Number(p.harga));
    const latest = prices[prices.length - 1];

    return NextResponse.json({
      commodity: {
        kode: latest.commodity.kodeKomoditas,
        nama: latest.commodity.namaDisplay,
      },
      region: {
        kode: latest.region.kodeWilayah,
        nama: latest.region.namaProvinsi,
      },
      data: prices.map((p) => ({
        tanggal: p.tanggal.toISOString().slice(0, 10),
        harga: Number(p.harga),
      })),
      summary: {
        hargaTerakhir: Number(latest.harga),
        perubahanHarian: latest.perubahanHarian ? Number(latest.perubahanHarian) : null,
        perubahanMingguan: latest.perubahanMingguan ? Number(latest.perubahanMingguan) : null,
        perubahanBulanan: latest.perubahanBulanan ? Number(latest.perubahanBulanan) : null,
        hargaTertinggi: Math.max(...hargaList),
        hargaTerendah: Math.min(...hargaList),
      },
    });
  } catch {
    return NextResponse.json({ commodity: null, region: null, data: [], summary: null, source: "mock" });
  }
}
