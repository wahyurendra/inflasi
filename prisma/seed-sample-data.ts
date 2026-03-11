import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

/**
 * Seed sample price data untuk 30 hari terakhir.
 * Data ini adalah simulasi realistis untuk demo/development.
 */
async function main() {
  console.log("Loading dimension data...");

  const regions = await prisma.dimRegion.findMany();
  const commodities = await prisma.dimCommodity.findMany();

  // Base prices per commodity (Rp)
  const basePrices: Record<string, number> = {
    BERAS: 14500,
    CABAI_MERAH: 52000,
    CABAI_RAWIT: 75000,
    BAWANG_MERAH: 38000,
    BAWANG_PUTIH: 37000,
    TELUR_AYAM: 27000,
    MINYAK_GORENG: 17800,
    GULA_PASIR: 16500,
  };

  // Trend multipliers (simulasi kenaikan menjelang Ramadan)
  const trendMultipliers: Record<string, number> = {
    BERAS: 0.001,
    CABAI_MERAH: 0.002,
    CABAI_RAWIT: 0.004, // Naik paling tajam
    BAWANG_MERAH: 0.003,
    BAWANG_PUTIH: 0.0005,
    TELUR_AYAM: 0.0015,
    MINYAK_GORENG: 0.0003,
    GULA_PASIR: 0.001,
  };

  // Regional price variation (% from national average)
  const regionalVariation: Record<string, number> = {
    "00": 0,      // Nasional
    "91": 0.15,   // Papua - lebih mahal
    "92": 0.12,   // Papua Barat
    "81": 0.10,   // Maluku
    "82": 0.08,   // Maluku Utara
    "53": 0.07,   // NTT
    "65": 0.05,   // Kaltara
    "64": 0.04,   // Kaltim
    "71": 0.03,   // Sulut
    "31": -0.02,  // Jakarta - sedikit lebih murah
    "35": -0.01,  // Jatim
    "33": -0.01,  // Jateng
  };

  const today = new Date();
  const days = 35; // 35 hari data

  console.log(`Seeding ${days} days of price data...`);

  let count = 0;

  for (let d = days; d >= 0; d--) {
    const date = new Date(today);
    date.setDate(date.getDate() - d);
    const dateStr = date.toISOString().slice(0, 10);
    const dayDate = new Date(dateStr);

    // Skip weekends (PIHPS doesn't update on weekends)
    if (date.getDay() === 0 || date.getDay() === 6) continue;

    for (const commodity of commodities) {
      const basePrice = basePrices[commodity.kodeKomoditas] || 15000;
      const trend = trendMultipliers[commodity.kodeKomoditas] || 0.001;

      // Select a subset of regions (nasional + 10 provinces for MVP)
      const mvpRegionCodes = [
        "00", "11", "12", "31", "32", "33", "35", "36",
        "51", "53", "64", "71", "73", "81", "91", "92",
      ];
      const selectedRegions = regions.filter((r) =>
        mvpRegionCodes.includes(r.kodeWilayah)
      );

      for (const region of selectedRegions) {
        const variation = regionalVariation[region.kodeWilayah] || (Math.random() - 0.5) * 0.04;
        const dayIndex = days - d;
        const trendEffect = basePrice * trend * dayIndex;
        const randomNoise = (Math.random() - 0.45) * basePrice * 0.02;
        const regionalEffect = basePrice * variation;

        const harga = Math.round(basePrice + trendEffect + randomNoise + regionalEffect);

        try {
          await prisma.factPriceDaily.upsert({
            where: {
              uq_price_daily: {
                tanggal: dayDate,
                regionId: region.id,
                commodityId: commodity.id,
              },
            },
            update: { harga },
            create: {
              tanggal: dayDate,
              regionId: region.id,
              commodityId: commodity.id,
              harga,
              sumber: "SAMPLE_DATA",
            },
          });
          count++;
        } catch {
          // Skip duplicates
        }
      }
    }
  }

  console.log(`Inserted ${count} price records.`);

  // Calculate price changes
  console.log("Calculating price changes...");
  await calculatePriceChanges();

  // Seed sample inflation data
  console.log("Seeding inflation data...");
  await seedInflation();

  // Generate alerts
  console.log("Generating sample alerts...");
  await seedAlerts();

  // Generate insight
  console.log("Generating sample insight...");
  await seedInsight();

  console.log("Sample data seeding complete!");
}

async function calculatePriceChanges() {
  // Update daily/weekly/monthly changes using SQL for performance
  await prisma.$executeRaw`
    UPDATE fact_price_daily fpd
    SET
      harga_kemarin = prev.harga,
      perubahan_harian = CASE
        WHEN prev.harga > 0 THEN ROUND(((fpd.harga - prev.harga) / prev.harga * 100)::numeric, 4)
        ELSE NULL
      END
    FROM (
      SELECT commodity_id, region_id, tanggal, harga,
        LEAD(tanggal) OVER (PARTITION BY commodity_id, region_id ORDER BY tanggal) AS next_date
      FROM fact_price_daily
    ) prev
    WHERE fpd.commodity_id = prev.commodity_id
      AND fpd.region_id = prev.region_id
      AND fpd.tanggal = prev.next_date
  `;

  // Weekly change
  await prisma.$executeRaw`
    UPDATE fact_price_daily fpd
    SET perubahan_mingguan = CASE
      WHEN w7.harga > 0 THEN ROUND(((fpd.harga - w7.harga) / w7.harga * 100)::numeric, 4)
      ELSE NULL
    END
    FROM fact_price_daily w7
    WHERE fpd.commodity_id = w7.commodity_id
      AND fpd.region_id = w7.region_id
      AND w7.tanggal = fpd.tanggal - INTERVAL '7 days'
  `;

  // Monthly change
  await prisma.$executeRaw`
    UPDATE fact_price_daily fpd
    SET perubahan_bulanan = CASE
      WHEN m30.harga > 0 THEN ROUND(((fpd.harga - m30.harga) / m30.harga * 100)::numeric, 4)
      ELSE NULL
    END
    FROM fact_price_daily m30
    WHERE fpd.commodity_id = m30.commodity_id
      AND fpd.region_id = m30.region_id
      AND m30.tanggal = fpd.tanggal - INTERVAL '30 days'
  `;
}

async function seedInflation() {
  const national = await prisma.dimRegion.findFirst({
    where: { kodeWilayah: "00" },
  });
  if (!national) return;

  const inflationData = [
    { periode: "2025-09-01", mtm: 0.18, ytd: 2.35, yoy: 4.82, ihk: 115.20 },
    { periode: "2025-10-01", mtm: 0.12, ytd: 2.47, yoy: 4.75, ihk: 115.34 },
    { periode: "2025-11-01", mtm: -0.05, ytd: 2.42, yoy: 4.68, ihk: 115.28 },
    { periode: "2025-12-01", mtm: 0.55, ytd: 2.98, yoy: 5.05, ihk: 115.91 },
    { periode: "2026-01-01", mtm: 0.65, ytd: 0.65, yoy: 5.15, ihk: 116.67 },
    { periode: "2026-02-01", mtm: 0.42, ytd: 1.07, yoy: 5.21, ihk: 118.35 },
  ];

  await prisma.factInflationMonthly.createMany({
    data: inflationData.map((data) => ({
      periode: new Date(data.periode),
      regionId: national.id,
      levelWilayah: "nasional",
      ihk: data.ihk,
      inflasiMtm: data.mtm,
      inflasiYtd: data.ytd,
      inflasiYoy: data.yoy,
      kelompok: "Makanan, Minuman dan Tembakau",
      sumber: "BPS",
    })),
    skipDuplicates: true,
  });

  if (false) {
  }
}

async function seedAlerts() {
  const regions = await prisma.dimRegion.findMany();
  const commodities = await prisma.dimCommodity.findMany();

  const getRegion = (kode: string) => regions.find((r) => r.kodeWilayah === kode)!;
  const getCommodity = (kode: string) => commodities.find((c) => c.kodeKomoditas === kode)!;

  const today = new Date().toISOString().slice(0, 10);
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);

  const alerts = [
    {
      tanggal: new Date(today),
      regionId: getRegion("00").id,
      commodityId: getCommodity("CABAI_RAWIT").id,
      alertType: "price_spike",
      severity: "critical",
      judul: "Cabai Rawit: Kenaikan 13.2% dalam 7 hari secara nasional",
      deskripsi: "Harga cabai rawit naik 13.2% dalam 7 hari terakhir (dari Rp 75.000 ke Rp 85.000/kg). Kenaikan terjadi di 12 dari 16 wilayah pemantauan. Tertinggi di Papua (+18%) dan Maluku (+15%). Faktor: menjelang Ramadan + curah hujan tinggi di sentra produksi.",
      nilaiAktual: 13.2,
      nilaiThreshold: 10.0,
    },
    {
      tanggal: new Date(yesterday),
      regionId: getRegion("00").id,
      commodityId: getCommodity("BAWANG_MERAH").id,
      alertType: "sustained_volatile",
      severity: "warning",
      judul: "Bawang Merah: Volatilitas tinggi 2 minggu berturut-turut",
      deskripsi: "Bawang merah menunjukkan CV 17.8% selama 14 hari terakhir (threshold: 15%). Harga berfluktuasi antara Rp 36.000 - Rp 44.000/kg secara nasional.",
      nilaiAktual: 17.8,
      nilaiThreshold: 15.0,
    },
    {
      tanggal: new Date(today),
      regionId: getRegion("91").id,
      commodityId: getCommodity("BERAS").id,
      alertType: "multi_commodity",
      severity: "critical",
      judul: "Papua: 4 komoditas naik >5% bersamaan",
      deskripsi: "Di Papua, 4 komoditas mengalami kenaikan >5% dalam 7 hari: cabai rawit (+18%), bawang merah (+8%), telur ayam (+7%), gula pasir (+6%). Perlu perhatian khusus terhadap distribusi dan stok.",
      nilaiAktual: 4,
      nilaiThreshold: 3,
    },
    {
      tanggal: new Date(yesterday),
      regionId: getRegion("81").id,
      commodityId: getCommodity("MINYAK_GORENG").id,
      alertType: "deviation",
      severity: "warning",
      judul: "Maluku: Minyak goreng 22% di atas median nasional",
      deskripsi: "Harga minyak goreng di Maluku (Rp 21.700/liter) berada 22% di atas median nasional (Rp 17.800/liter). Kemungkinan terkait biaya distribusi dan keterbatasan pasokan.",
      nilaiAktual: 22.0,
      nilaiThreshold: 20.0,
    },
    {
      tanggal: new Date(today),
      regionId: getRegion("32").id,
      commodityId: getCommodity("CABAI_RAWIT").id,
      alertType: "price_rise",
      severity: "warning",
      judul: "Jawa Barat: Cabai rawit naik 8.5% dalam 7 hari",
      deskripsi: "Harga cabai rawit di Jawa Barat naik 8.5% (dari Rp 78.000 ke Rp 84.600/kg). Curah hujan tinggi mengganggu pasokan dari sentra produksi Garut dan Cianjur.",
      nilaiAktual: 8.5,
      nilaiThreshold: 5.0,
    },
  ];

  for (const alert of alerts) {
    await prisma.analyticsAlert.create({ data: alert });
  }
}

async function seedInsight() {
  const today = new Date().toISOString().slice(0, 10);

  await prisma.analyticsInsight.create({
    data: {
      tanggal: new Date(today),
      tipe: "harian",
      judul: `Insight Harian — ${today}`,
      konten: `RINGKASAN:
Tekanan harga pangan meningkat menjelang Ramadan. Cabai rawit menjadi komoditas dengan kenaikan tertinggi minggu ini (+13.2%), diikuti bawang merah (+7.5%) dan telur ayam (+4.2%).

KOMODITAS PERLU DIPERHATIKAN:
- Cabai rawit: Rp 85.000/kg (+13.2% w/w). Kenaikan terjadi di 12 dari 16 wilayah. Tertinggi: Papua Rp 98.000/kg.
- Bawang merah: Rp 42.000/kg (+7.5% w/w). Volatilitas tinggi 2 minggu berturut-turut (CV 17.8%).
- Telur ayam: Rp 28.500/kg (+4.2% w/w). Kenaikan merata nasional.

WILAYAH PERLU DIPERHATIKAN:
- Papua: 4 komoditas naik >5% bersamaan — risiko TINGGI
- Maluku: Minyak goreng dan beras deviasi tinggi dari median nasional
- Jawa Barat: Cabai rawit naik 8.5%, terkait curah hujan tinggi di sentra produksi

KONTEKS:
- Ramadan diperkirakan mulai ~22 Maret 2026
- Panen raya beras sedang berlangsung — tekanan harga beras relatif terkendali
- Kurs USD/IDR stabil di kisaran Rp 15.850

Sumber: PIHPS BI, BPS | Periode: ${today}`,
    },
  });
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });
