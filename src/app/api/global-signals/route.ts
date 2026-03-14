import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET() {
  try {
    const [faoData, commodityData, kursData, energyData, gscpiData, newsData] =
      await Promise.all([
        prisma.extFaoFoodPrice.findMany({
          orderBy: { periode: "desc" },
          take: 12,
        }),
        prisma.extCommodityPrice.findMany({
          orderBy: { periode: "desc" },
          take: 48,
        }),
        prisma.extExchangeRate.findMany({
          orderBy: { tanggal: "desc" },
          take: 30,
        }),
        prisma.extEnergyPrice.findMany({
          orderBy: { tanggal: "desc" },
          take: 12,
        }),
        prisma.extSupplyChainIndex.findMany({
          orderBy: { periode: "desc" },
          take: 12,
        }),
        prisma.extNewsSignal.findMany({
          orderBy: { tanggal: "desc" },
          take: 20,
        }),
      ]);

    const fao = faoData.map((r) => ({
      periode: r.periode.toISOString().slice(0, 10),
      overall: r.indexOverall ? Number(r.indexOverall) : null,
      cereals: r.indexCereals ? Number(r.indexCereals) : null,
      vegOil: r.indexVegOil ? Number(r.indexVegOil) : null,
      dairy: r.indexDairy ? Number(r.indexDairy) : null,
      meat: r.indexMeat ? Number(r.indexMeat) : null,
      sugar: r.indexSugar ? Number(r.indexSugar) : null,
    }));

    const latestCommodities: Record<string, { price: number; changePct: number | null; unit: string; periode: string }> = {};
    for (const c of commodityData) {
      if (!latestCommodities[c.commodity]) {
        latestCommodities[c.commodity] = {
          price: Number(c.price),
          changePct: c.changePct ? Number(c.changePct) : null,
          unit: c.unit,
          periode: c.periode.toISOString().slice(0, 10),
        };
      }
    }

    const kurs = kursData.map((r) => ({
      tanggal: r.tanggal.toISOString().slice(0, 10),
      kursTengah: r.kursTengah ? Number(r.kursTengah) : null,
      changePct: r.changePct ? Number(r.changePct) : null,
    }));

    const energy = energyData.map((r) => ({
      tanggal: r.tanggal.toISOString().slice(0, 10),
      commodity: r.commodity,
      price: Number(r.price),
      changePct: r.changePct ? Number(r.changePct) : null,
    }));

    const supplyChain = gscpiData.map((r) => ({
      periode: r.periode.toISOString().slice(0, 10),
      gscpi: Number(r.gscpi),
    }));

    const news = newsData.map((r) => ({
      tanggal: r.tanggal.toISOString().slice(0, 10),
      kategori: r.kategori,
      judul: r.judul,
      sumber: r.sumber,
      url: r.url,
      sentimen: r.sentimen,
      relevansi: r.relevansi ? Number(r.relevansi) : null,
    }));

    return NextResponse.json({
      fao,
      commodities: latestCommodities,
      kurs,
      energy,
      supplyChain,
      news,
    });
  } catch (error) {
    console.error("Global signals error:", error);
    return NextResponse.json({ error: "Database error" }, { status: 500 });
  }
}
