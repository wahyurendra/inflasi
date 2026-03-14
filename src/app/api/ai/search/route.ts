import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

/**
 * Lightweight RAG search endpoint.
 * Extracts keywords from natural language query and returns structured data context.
 * No vector DB needed — uses SQL queries against existing tables.
 */

const COMMODITY_KEYWORDS: Record<string, string> = {
  beras: "BERAS",
  cabai: "CABAI_RAWIT",
  "cabai rawit": "CABAI_RAWIT",
  "cabai merah": "CABAI_MERAH",
  "bawang merah": "BAWANG_MERAH",
  "bawang putih": "BAWANG_PUTIH",
  telur: "TELUR_AYAM",
  "minyak goreng": "MINYAK_GORENG",
  gula: "GULA_PASIR",
};

export async function POST(request: NextRequest) {
  try {
    const { query } = await request.json();
    if (!query) {
      return NextResponse.json({ error: "query is required" }, { status: 400 });
    }

    const lowerQuery = query.toLowerCase();
    const context: Record<string, unknown> = {};

    // 1. Detect commodity mentions
    const matchedCommodity = Object.entries(COMMODITY_KEYWORDS).find(([keyword]) =>
      lowerQuery.includes(keyword)
    );

    if (matchedCommodity) {
      const [, kode] = matchedCommodity;
      const commodity = await prisma.dimCommodity.findFirst({
        where: { kodeKomoditas: kode },
      });

      if (commodity) {
        const prices = await prisma.factPriceDaily.findMany({
          where: { commodityId: commodity.id },
          orderBy: { tanggal: "desc" },
          take: 14,
          include: { region: true },
        });

        context.hargaKomoditas = prices.map((p) => ({
          tanggal: p.tanggal.toISOString().slice(0, 10),
          wilayah: p.region.namaProvinsi,
          harga: Number(p.harga),
          perubahanHarian: p.perubahanHarian ? Number(p.perubahanHarian) : null,
          perubahanMingguan: p.perubahanMingguan ? Number(p.perubahanMingguan) : null,
        }));

        // Get forecasts
        const forecasts = await prisma.analyticsForecast.findMany({
          where: { commodityId: commodity.id, tanggal: { gte: new Date() } },
          orderBy: { tanggal: "asc" },
          take: 14,
        }).catch(() => []);

        if (forecasts.length) {
          context.forecast = forecasts.map((f) => ({
            tanggal: f.tanggal.toISOString().slice(0, 10),
            prediksi: Number(f.yhat),
          }));
        }
      }
    }

    // 2. Check for alert-related queries
    if (lowerQuery.includes("alert") || lowerQuery.includes("peringatan") || lowerQuery.includes("risiko")) {
      const alerts = await prisma.analyticsAlert.findMany({
        where: { isActive: true },
        include: { commodity: true, region: true },
        orderBy: { tanggal: "desc" },
        take: 5,
      });

      context.alertAktif = alerts.map((a) => ({
        judul: a.judul,
        deskripsi: a.deskripsi,
        severity: a.severity,
        komoditas: a.commodity.namaDisplay,
        wilayah: a.region.namaProvinsi,
      }));
    }

    // 3. Check for forecast-related queries
    if (lowerQuery.includes("prediksi") || lowerQuery.includes("forecast") || lowerQuery.includes("minggu depan")) {
      const forecasts = await prisma.analyticsForecast.findMany({
        where: { tanggal: { gte: new Date() }, horizon: 14 },
        include: { commodity: true },
        orderBy: { tanggal: "asc" },
        take: 20,
      }).catch(() => []);

      context.semuaForecast = forecasts.map((f) => ({
        komoditas: f.commodity.namaDisplay,
        tanggal: f.tanggal.toISOString().slice(0, 10),
        prediksi: Number(f.yhat),
        bawah: Number(f.yhatLower),
        atas: Number(f.yhatUpper),
      }));
    }

    return NextResponse.json({ context, query });
  } catch {
    return NextResponse.json({ context: {}, query: "" });
  }
}
