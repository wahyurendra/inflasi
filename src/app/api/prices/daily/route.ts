import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const commodity = searchParams.get("commodity");
  const region = searchParams.get("region") || "00";
  const days = parseInt(searchParams.get("days") || "30");

  try {
    const since = new Date();
    since.setDate(since.getDate() - days);

    const prices = await prisma.factPriceDaily.findMany({
      where: {
        commodity: commodity ? { kodeKomoditas: commodity } : undefined,
        region: { kodeWilayah: region },
        tanggal: { gte: since },
      },
      include: {
        commodity: true,
        region: true,
      },
      orderBy: { tanggal: "desc" },
    });

    return NextResponse.json({
      data: prices.map((p) => ({
        tanggal: p.tanggal.toISOString().slice(0, 10),
        harga: Number(p.harga),
        perubahanHarian: p.perubahanHarian ? Number(p.perubahanHarian) : null,
        perubahanMingguan: p.perubahanMingguan ? Number(p.perubahanMingguan) : null,
        perubahanBulanan: p.perubahanBulanan ? Number(p.perubahanBulanan) : null,
        commodity: {
          kode: p.commodity.kodeKomoditas,
          nama: p.commodity.namaDisplay,
        },
        region: {
          kode: p.region.kodeWilayah,
          nama: p.region.namaProvinsi,
        },
      })),
      count: prices.length,
    });
  } catch {
    // DB not connected — return empty
    return NextResponse.json({ data: [], count: 0, source: "mock" });
  }
}
