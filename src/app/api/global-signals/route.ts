import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

// Mock data for when DB is unavailable
function getMockData() {
  const months = Array.from({ length: 12 }, (_, i) => {
    const d = new Date(2026, 1 - i, 1);
    return d.toISOString().slice(0, 10);
  });

  const fao = months.map((p, i) => ({
    periode: p,
    overall: 130.1 - i * 0.8,
    cereals: 122.0 - i * 0.5,
    vegOil: 143.5 - i * 1.2,
    dairy: 133.0 - i * 0.6,
    meat: 118.0 - i * 0.3,
    sugar: 132.0 - i * 0.4,
  }));

  const commodities: Record<string, { price: number; changePct: number | null; unit: string; periode: string }> = {
    rice: { price: 572, changePct: 1.2, unit: "USD/mt", periode: "2026-02-01" },
    wheat: { price: 275, changePct: 1.8, unit: "USD/mt", periode: "2026-02-01" },
    palm_oil: { price: 1170, changePct: 1.3, unit: "USD/mt", periode: "2026-02-01" },
    sugar: { price: 0.54, changePct: 1.9, unit: "USD/kg", periode: "2026-02-01" },
    urea: { price: 370, changePct: 2.2, unit: "USD/mt", periode: "2026-02-01" },
    crude_oil_brent: { price: 79.8, changePct: 3.6, unit: "USD/bbl", periode: "2026-02-01" },
  };

  const days30 = Array.from({ length: 30 }, (_, i) => {
    const d = new Date(2026, 2, 10 - i);
    return d.toISOString().slice(0, 10);
  });

  const kurs = days30.map((t, i) => ({
    tanggal: t,
    kursTengah: 16250 + Math.round(Math.sin(i * 0.3) * 150),
    changePct: i === 0 ? null : +(Math.random() * 0.6 - 0.3).toFixed(2),
  }));

  const energy = [
    { tanggal: "2026-03-01", commodity: "brent", price: 83.5, changePct: 4.6 },
    { tanggal: "2026-02-01", commodity: "brent", price: 79.8, changePct: 3.6 },
    { tanggal: "2026-01-01", commodity: "brent", price: 77.0, changePct: 3.4 },
  ];

  const supplyChain = [
    { periode: "2026-02-01", gscpi: 0.75 },
    { periode: "2026-01-01", gscpi: 0.68 },
    { periode: "2025-12-01", gscpi: 0.55 },
    { periode: "2025-11-01", gscpi: 0.48 },
    { periode: "2025-10-01", gscpi: 0.52 },
    { periode: "2025-09-01", gscpi: 0.45 },
    { periode: "2025-08-01", gscpi: 0.30 },
    { periode: "2025-07-01", gscpi: 0.25 },
    { periode: "2025-06-01", gscpi: 0.08 },
    { periode: "2025-05-01", gscpi: 0.15 },
    { periode: "2025-04-01", gscpi: 0.22 },
    { periode: "2025-03-01", gscpi: 0.18 },
  ];

  const news = [
    { tanggal: "2026-03-10", kategori: "food_supply", judul: "India extends rice export restrictions amid global supply concerns", sumber: "Reuters", url: null, sentimen: "negative", relevansi: 85 },
    { tanggal: "2026-03-09", kategori: "energy", judul: "OPEC+ considers production cut extension through Q2 2026", sumber: "Bloomberg", url: null, sentimen: "negative", relevansi: 78 },
    { tanggal: "2026-03-08", kategori: "climate", judul: "La Niña conditions strengthen across Pacific, threatening SE Asian harvests", sumber: "WMO", url: null, sentimen: "negative", relevansi: 90 },
    { tanggal: "2026-03-07", kategori: "agriculture", judul: "Palm oil output falls 8% in Malaysia due to labor shortages", sumber: "MPOB", url: null, sentimen: "negative", relevansi: 82 },
    { tanggal: "2026-03-06", kategori: "geopolitics", judul: "Black Sea grain corridor agreement renewal faces uncertainty", sumber: "AP", url: null, sentimen: "negative", relevansi: 75 },
    { tanggal: "2026-03-05", kategori: "indonesia", judul: "BI pertahankan suku bunga acuan di 5.75% untuk stabilitas rupiah", sumber: "Bisnis Indonesia", url: null, sentimen: "neutral", relevansi: 88 },
    { tanggal: "2026-03-04", kategori: "food_supply", judul: "Thailand rice exports surge 12% YoY in February 2026", sumber: "Bangkok Post", url: null, sentimen: "positive", relevansi: 80 },
    { tanggal: "2026-03-03", kategori: "climate", judul: "Banjir di Jawa Tengah ancam produksi beras musim tanam kedua", sumber: "BMKG", url: null, sentimen: "negative", relevansi: 92 },
  ];

  return { fao, commodities, kurs, energy, supplyChain, news, source: "mock" as const };
}

export async function GET() {
  try {
    // Fetch all global signals in parallel
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

    // If no data in DB, return mock
    if (faoData.length === 0 && commodityData.length === 0) {
      return NextResponse.json(getMockData());
    }

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
      source: "database",
    });
  } catch {
    // DB unavailable — return mock data
    return NextResponse.json(getMockData());
  }
}
