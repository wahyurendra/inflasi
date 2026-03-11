import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  console.log("Seeding dim_region...");
  await seedRegions();

  console.log("Seeding dim_commodity...");
  await seedCommodities();

  console.log("Seeding dim_calendar...");
  await seedCalendar();

  console.log("Seed complete.");
}

async function seedRegions() {
  const regions = [
    { kodeWilayah: "00", namaProvinsi: "Nasional", levelWilayah: "nasional", latitude: -2.5, longitude: 118.0 },
    { kodeWilayah: "11", namaProvinsi: "Aceh", levelWilayah: "provinsi", latitude: 4.695, longitude: 96.749 },
    { kodeWilayah: "12", namaProvinsi: "Sumatera Utara", levelWilayah: "provinsi", latitude: 2.116, longitude: 99.545 },
    { kodeWilayah: "13", namaProvinsi: "Sumatera Barat", levelWilayah: "provinsi", latitude: -0.739, longitude: 100.8 },
    { kodeWilayah: "14", namaProvinsi: "Riau", levelWilayah: "provinsi", latitude: 1.059, longitude: 102.144 },
    { kodeWilayah: "15", namaProvinsi: "Jambi", levelWilayah: "provinsi", latitude: -1.611, longitude: 103.607 },
    { kodeWilayah: "16", namaProvinsi: "Sumatera Selatan", levelWilayah: "provinsi", latitude: -3.319, longitude: 103.914 },
    { kodeWilayah: "17", namaProvinsi: "Bengkulu", levelWilayah: "provinsi", latitude: -3.792, longitude: 102.26 },
    { kodeWilayah: "18", namaProvinsi: "Lampung", levelWilayah: "provinsi", latitude: -4.559, longitude: 105.406 },
    { kodeWilayah: "19", namaProvinsi: "Kepulauan Bangka Belitung", levelWilayah: "provinsi", latitude: -2.741, longitude: 106.44 },
    { kodeWilayah: "21", namaProvinsi: "Kepulauan Riau", levelWilayah: "provinsi", latitude: 3.946, longitude: 108.143 },
    { kodeWilayah: "31", namaProvinsi: "DKI Jakarta", levelWilayah: "provinsi", latitude: -6.175, longitude: 106.827 },
    { kodeWilayah: "32", namaProvinsi: "Jawa Barat", levelWilayah: "provinsi", latitude: -6.889, longitude: 107.61 },
    { kodeWilayah: "33", namaProvinsi: "Jawa Tengah", levelWilayah: "provinsi", latitude: -7.15, longitude: 110.14 },
    { kodeWilayah: "34", namaProvinsi: "DI Yogyakarta", levelWilayah: "provinsi", latitude: -7.797, longitude: 110.369 },
    { kodeWilayah: "35", namaProvinsi: "Jawa Timur", levelWilayah: "provinsi", latitude: -7.536, longitude: 112.238 },
    { kodeWilayah: "36", namaProvinsi: "Banten", levelWilayah: "provinsi", latitude: -6.405, longitude: 106.064 },
    { kodeWilayah: "51", namaProvinsi: "Bali", levelWilayah: "provinsi", latitude: -8.352, longitude: 115.092 },
    { kodeWilayah: "52", namaProvinsi: "Nusa Tenggara Barat", levelWilayah: "provinsi", latitude: -8.652, longitude: 117.362 },
    { kodeWilayah: "53", namaProvinsi: "Nusa Tenggara Timur", levelWilayah: "provinsi", latitude: -8.658, longitude: 121.079 },
    { kodeWilayah: "61", namaProvinsi: "Kalimantan Barat", levelWilayah: "provinsi", latitude: -0.278, longitude: 109.341 },
    { kodeWilayah: "62", namaProvinsi: "Kalimantan Tengah", levelWilayah: "provinsi", latitude: -1.682, longitude: 113.382 },
    { kodeWilayah: "63", namaProvinsi: "Kalimantan Selatan", levelWilayah: "provinsi", latitude: -3.092, longitude: 115.283 },
    { kodeWilayah: "64", namaProvinsi: "Kalimantan Timur", levelWilayah: "provinsi", latitude: 1.693, longitude: 116.419 },
    { kodeWilayah: "65", namaProvinsi: "Kalimantan Utara", levelWilayah: "provinsi", latitude: 3.073, longitude: 116.041 },
    { kodeWilayah: "71", namaProvinsi: "Sulawesi Utara", levelWilayah: "provinsi", latitude: 0.625, longitude: 123.975 },
    { kodeWilayah: "72", namaProvinsi: "Sulawesi Tengah", levelWilayah: "provinsi", latitude: -1.43, longitude: 121.446 },
    { kodeWilayah: "73", namaProvinsi: "Sulawesi Selatan", levelWilayah: "provinsi", latitude: -3.669, longitude: 119.974 },
    { kodeWilayah: "74", namaProvinsi: "Sulawesi Tenggara", levelWilayah: "provinsi", latitude: -4.145, longitude: 122.175 },
    { kodeWilayah: "75", namaProvinsi: "Gorontalo", levelWilayah: "provinsi", latitude: 0.544, longitude: 123.057 },
    { kodeWilayah: "76", namaProvinsi: "Sulawesi Barat", levelWilayah: "provinsi", latitude: -2.844, longitude: 119.232 },
    { kodeWilayah: "81", namaProvinsi: "Maluku", levelWilayah: "provinsi", latitude: -3.239, longitude: 130.145 },
    { kodeWilayah: "82", namaProvinsi: "Maluku Utara", levelWilayah: "provinsi", latitude: 1.571, longitude: 127.809 },
    { kodeWilayah: "91", namaProvinsi: "Papua", levelWilayah: "provinsi", latitude: -4.269, longitude: 138.08 },
    { kodeWilayah: "92", namaProvinsi: "Papua Barat", levelWilayah: "provinsi", latitude: -1.338, longitude: 133.174 },
  ];

  for (const region of regions) {
    await prisma.dimRegion.upsert({
      where: { kodeWilayah: region.kodeWilayah },
      update: {},
      create: region,
    });
  }
}

async function seedCommodities() {
  const commodities = [
    { kodeKomoditas: "BERAS", namaKomoditas: "Beras", namaDisplay: "Beras", kategori: "bahan_pokok", satuan: "kg", isStrategis: true },
    { kodeKomoditas: "CABAI_MERAH", namaKomoditas: "Cabai Merah", namaDisplay: "Cabai Merah", kategori: "bumbu", satuan: "kg", isStrategis: true },
    { kodeKomoditas: "CABAI_RAWIT", namaKomoditas: "Cabai Rawit", namaDisplay: "Cabai Rawit", kategori: "bumbu", satuan: "kg", isStrategis: true },
    { kodeKomoditas: "BAWANG_MERAH", namaKomoditas: "Bawang Merah", namaDisplay: "Bawang Merah", kategori: "bumbu", satuan: "kg", isStrategis: true },
    { kodeKomoditas: "BAWANG_PUTIH", namaKomoditas: "Bawang Putih", namaDisplay: "Bawang Putih", kategori: "bumbu", satuan: "kg", isStrategis: true },
    { kodeKomoditas: "TELUR_AYAM", namaKomoditas: "Telur Ayam Ras", namaDisplay: "Telur Ayam", kategori: "protein", satuan: "kg", isStrategis: true },
    { kodeKomoditas: "MINYAK_GORENG", namaKomoditas: "Minyak Goreng", namaDisplay: "Minyak Goreng", kategori: "minyak_gula", satuan: "liter", isStrategis: true },
    { kodeKomoditas: "GULA_PASIR", namaKomoditas: "Gula Pasir", namaDisplay: "Gula Pasir", kategori: "minyak_gula", satuan: "kg", isStrategis: true },
  ];

  for (const commodity of commodities) {
    await prisma.dimCommodity.upsert({
      where: { kodeKomoditas: commodity.kodeKomoditas },
      update: {},
      create: commodity,
    });
  }
}

async function seedCalendar() {
  const startDate = new Date("2024-01-01");
  const endDate = new Date("2027-12-31");
  const namaHari = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"];

  // Hari libur nasional utama (simplified - bisa diperkaya)
  const holidays: Record<string, string> = {
    // 2025
    "2025-01-01": "Tahun Baru",
    "2025-03-29": "Hari Raya Nyepi",
    "2025-03-30": "Idul Fitri 1446H",
    "2025-03-31": "Idul Fitri 1446H",
    "2025-05-01": "Hari Buruh",
    "2025-06-01": "Hari Lahir Pancasila",
    "2025-06-06": "Idul Adha 1446H",
    "2025-08-17": "Hari Kemerdekaan",
    "2025-12-25": "Natal",
    // 2026
    "2026-01-01": "Tahun Baru",
    "2026-03-20": "Idul Fitri 1447H",
    "2026-03-21": "Idul Fitri 1447H",
    "2026-05-01": "Hari Buruh",
    "2026-05-27": "Idul Adha 1447H",
    "2026-06-01": "Hari Lahir Pancasila",
    "2026-08-17": "Hari Kemerdekaan",
    "2026-12-25": "Natal",
  };

  // Musim Ramadan (approx dates)
  const ramadanPeriods = [
    { start: "2025-03-01", end: "2025-03-29" },
    { start: "2026-02-18", end: "2026-03-19" },
    { start: "2027-02-08", end: "2027-03-09" },
  ];

  // Nataru (Natal + Tahun Baru) periods
  const nataruPeriods = [
    { start: "2024-12-20", end: "2025-01-05" },
    { start: "2025-12-20", end: "2026-01-05" },
    { start: "2026-12-20", end: "2027-01-05" },
    { start: "2027-12-20", end: "2027-12-31" },
  ];

  // Panen raya beras (Feb-Apr dan Jul-Sep approx)
  const panenPeriods = [
    { start: "2025-02-01", end: "2025-04-30" },
    { start: "2025-07-01", end: "2025-09-30" },
    { start: "2026-02-01", end: "2026-04-30" },
    { start: "2026-07-01", end: "2026-09-30" },
    { start: "2027-02-01", end: "2027-04-30" },
    { start: "2027-07-01", end: "2027-09-30" },
  ];

  function getMusim(dateStr: string): string {
    for (const p of ramadanPeriods) {
      if (dateStr >= p.start && dateStr <= p.end) return "ramadan";
    }
    // Check if it's Idulfitri (1-2 days after Ramadan end)
    for (const p of ramadanPeriods) {
      const endDate = new Date(p.end);
      const after1 = new Date(endDate);
      after1.setDate(after1.getDate() + 1);
      const after2 = new Date(endDate);
      after2.setDate(after2.getDate() + 2);
      const d1 = after1.toISOString().slice(0, 10);
      const d2 = after2.toISOString().slice(0, 10);
      if (dateStr === d1 || dateStr === d2) return "idulfitri";
    }
    for (const p of nataruPeriods) {
      if (dateStr >= p.start && dateStr <= p.end) return "nataru";
    }
    for (const p of panenPeriods) {
      if (dateStr >= p.start && dateStr <= p.end) return "panen_raya";
    }
    return "normal";
  }

  function getWeekOfYear(date: Date): number {
    const start = new Date(date.getFullYear(), 0, 1);
    const diff = date.getTime() - start.getTime();
    return Math.ceil((diff / 86400000 + start.getDay() + 1) / 7);
  }

  // Batch insert for performance
  const batchSize = 500;
  let batch: Array<{
    tanggal: Date;
    tahun: number;
    bulan: number;
    mingguKe: number;
    hariKe: number;
    namaHari: string;
    isWeekend: boolean;
    isHariLibur: boolean;
    namaLibur: string | null;
    musim: string;
  }> = [];

  const current = new Date(startDate);
  while (current <= endDate) {
    const dateStr = current.toISOString().slice(0, 10);
    const dayOfWeek = current.getDay();

    batch.push({
      tanggal: new Date(dateStr),
      tahun: current.getFullYear(),
      bulan: current.getMonth() + 1,
      mingguKe: getWeekOfYear(current),
      hariKe: dayOfWeek,
      namaHari: namaHari[dayOfWeek],
      isWeekend: dayOfWeek === 0 || dayOfWeek === 6,
      isHariLibur: dateStr in holidays,
      namaLibur: holidays[dateStr] || null,
      musim: getMusim(dateStr),
    });

    if (batch.length >= batchSize) {
      await prisma.dimCalendar.createMany({ data: batch, skipDuplicates: true });
      batch = [];
    }

    current.setDate(current.getDate() + 1);
  }

  if (batch.length > 0) {
    await prisma.dimCalendar.createMany({ data: batch, skipDuplicates: true });
  }
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
