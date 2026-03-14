// ============================================================
// Komoditas MVP
// ============================================================

export const MVP_COMMODITIES = [
  {
    kode: "BERAS",
    nama: "Beras",
    display: "Beras",
    kategori: "bahan_pokok",
    satuan: "kg",
    strategis: true,
  },
  {
    kode: "CABAI_MERAH",
    nama: "Cabai Merah",
    display: "Cabai Merah",
    kategori: "bumbu",
    satuan: "kg",
    strategis: true,
  },
  {
    kode: "CABAI_RAWIT",
    nama: "Cabai Rawit",
    display: "Cabai Rawit",
    kategori: "bumbu",
    satuan: "kg",
    strategis: true,
  },
  {
    kode: "BAWANG_MERAH",
    nama: "Bawang Merah",
    display: "Bawang Merah",
    kategori: "bumbu",
    satuan: "kg",
    strategis: true,
  },
  {
    kode: "BAWANG_PUTIH",
    nama: "Bawang Putih",
    display: "Bawang Putih",
    kategori: "bumbu",
    satuan: "kg",
    strategis: true,
  },
  {
    kode: "TELUR_AYAM",
    nama: "Telur Ayam Ras",
    display: "Telur Ayam",
    kategori: "protein",
    satuan: "kg",
    strategis: true,
  },
  {
    kode: "MINYAK_GORENG",
    nama: "Minyak Goreng",
    display: "Minyak Goreng",
    kategori: "minyak_gula",
    satuan: "liter",
    strategis: true,
  },
  {
    kode: "GULA_PASIR",
    nama: "Gula Pasir",
    display: "Gula Pasir",
    kategori: "minyak_gula",
    satuan: "kg",
    strategis: true,
  },
  {
    kode: "DAGING_AYAM",
    nama: "Daging Ayam Ras",
    display: "Daging Ayam",
    kategori: "protein",
    satuan: "kg",
    strategis: true,
  },
  {
    kode: "DAGING_SAPI",
    nama: "Daging Sapi",
    display: "Daging Sapi",
    kategori: "protein",
    satuan: "kg",
    strategis: true,
  },
] as const;

// ============================================================
// Wilayah — 34 Provinsi + Nasional (Kode BPS)
// ============================================================

export const REGIONS = [
  { kode: "00", provinsi: "Nasional", level: "nasional" },
  { kode: "11", provinsi: "Aceh", level: "provinsi" },
  { kode: "12", provinsi: "Sumatera Utara", level: "provinsi" },
  { kode: "13", provinsi: "Sumatera Barat", level: "provinsi" },
  { kode: "14", provinsi: "Riau", level: "provinsi" },
  { kode: "15", provinsi: "Jambi", level: "provinsi" },
  { kode: "16", provinsi: "Sumatera Selatan", level: "provinsi" },
  { kode: "17", provinsi: "Bengkulu", level: "provinsi" },
  { kode: "18", provinsi: "Lampung", level: "provinsi" },
  { kode: "19", provinsi: "Kepulauan Bangka Belitung", level: "provinsi" },
  { kode: "21", provinsi: "Kepulauan Riau", level: "provinsi" },
  { kode: "31", provinsi: "DKI Jakarta", level: "provinsi" },
  { kode: "32", provinsi: "Jawa Barat", level: "provinsi" },
  { kode: "33", provinsi: "Jawa Tengah", level: "provinsi" },
  { kode: "34", provinsi: "DI Yogyakarta", level: "provinsi" },
  { kode: "35", provinsi: "Jawa Timur", level: "provinsi" },
  { kode: "36", provinsi: "Banten", level: "provinsi" },
  { kode: "51", provinsi: "Bali", level: "provinsi" },
  { kode: "52", provinsi: "Nusa Tenggara Barat", level: "provinsi" },
  { kode: "53", provinsi: "Nusa Tenggara Timur", level: "provinsi" },
  { kode: "61", provinsi: "Kalimantan Barat", level: "provinsi" },
  { kode: "62", provinsi: "Kalimantan Tengah", level: "provinsi" },
  { kode: "63", provinsi: "Kalimantan Selatan", level: "provinsi" },
  { kode: "64", provinsi: "Kalimantan Timur", level: "provinsi" },
  { kode: "65", provinsi: "Kalimantan Utara", level: "provinsi" },
  { kode: "71", provinsi: "Sulawesi Utara", level: "provinsi" },
  { kode: "72", provinsi: "Sulawesi Tengah", level: "provinsi" },
  { kode: "73", provinsi: "Sulawesi Selatan", level: "provinsi" },
  { kode: "74", provinsi: "Sulawesi Tenggara", level: "provinsi" },
  { kode: "75", provinsi: "Gorontalo", level: "provinsi" },
  { kode: "76", provinsi: "Sulawesi Barat", level: "provinsi" },
  { kode: "81", provinsi: "Maluku", level: "provinsi" },
  { kode: "82", provinsi: "Maluku Utara", level: "provinsi" },
  { kode: "91", provinsi: "Papua", level: "provinsi" },
  { kode: "92", provinsi: "Papua Barat", level: "provinsi" },
] as const;

// ============================================================
// Alert Thresholds
// ============================================================

export const ALERT_THRESHOLDS = {
  PRICE_SPIKE_7D_PCT: 10,
  PRICE_RISE_7D_PCT: 5,
  REGIONAL_DEVIATION_PCT: 20,
  VOLATILITY_CV_14D: 15,
  WEATHER_PRICE_COMBO_PCT: 3,
  MULTI_COMMODITY_COUNT: 3,
  MULTI_COMMODITY_PCT: 5,
} as const;

// ============================================================
// Risk Score Weights
// ============================================================

export const RISK_WEIGHTS = {
  kenaikan7d: 0.25,
  kenaikan30d: 0.2,
  volatilitas: 0.2,
  deviasiWilayah: 0.15,
  sinyalCuaca: 0.1,
  sinyalStok: 0.1,
} as const;

// ============================================================
// Navigation
// ============================================================

export const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: "LayoutDashboard" },
  { href: "/komoditas", label: "Harga Komoditas", icon: "TrendingUp" },
  { href: "/wilayah", label: "Peta Wilayah", icon: "Map" },
  { href: "/alerts", label: "Alert Center", icon: "AlertTriangle" },
  { href: "/ai", label: "AI Assistant", icon: "MessageSquare" },
] as const;
