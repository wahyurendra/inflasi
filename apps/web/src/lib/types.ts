// ============================================================
// Shared TypeScript types for INFLASI platform
// ============================================================

// --- Dimension Types ---

export interface Region {
  id: number;
  kodeWilayah: string;
  namaProvinsi: string;
  namaKabKota: string | null;
  levelWilayah: "nasional" | "provinsi" | "kab_kota";
  latitude: number | null;
  longitude: number | null;
}

export interface Commodity {
  id: number;
  kodeKomoditas: string;
  namaKomoditas: string;
  namaDisplay: string;
  kategori: "bahan_pokok" | "bumbu" | "protein" | "minyak_gula";
  satuan: string;
  isStrategis: boolean;
}

// --- Fact Types ---

export interface InflationMonthly {
  periode: string; // ISO date
  region: Region;
  levelWilayah: string;
  ihk: number | null;
  inflasiMtm: number | null;
  inflasiYtd: number | null;
  inflasiYoy: number | null;
  kelompok: string | null;
  commodity: Commodity | null;
  andil: number | null;
  sumber: string;
}

export interface PriceDaily {
  tanggal: string; // ISO date
  region: Region;
  commodity: Commodity;
  harga: number;
  hargaKemarin: number | null;
  perubahanHarian: number | null;
  perubahanMingguan: number | null;
  perubahanBulanan: number | null;
  sumber: string;
}

export interface SupplyStock {
  tanggal: string;
  region: Region;
  commodity: Commodity;
  stok: number | null;
  cadangan: number | null;
  status: "aman" | "waspada" | "kritis" | null;
}

export interface MacroDriver {
  tanggal: string;
  kursUsdIdr: number | null;
  kursChangePct: number | null;
  hargaBbm: number | null;
}

export interface Climate {
  tanggal: string;
  region: Region;
  curahHujan: number | null;
  suhuRata: number | null;
  anomaliCuaca: string | null;
  warningLevel: "normal" | "waspada" | "siaga" | "awas" | null;
}

// --- Analytics Types ---

export interface RiskScore {
  tanggal: string;
  region: Region;
  commodity: Commodity;
  skorKenaikan7d: number;
  skorKenaikan30d: number;
  skorVolatilitas: number;
  skorDeviasiWilayah: number;
  skorCuaca: number;
  skorStok: number;
  riskScoreTotal: number;
  riskCategory: "rendah" | "sedang" | "tinggi";
}

export type AlertType =
  | "price_spike"
  | "price_rise"
  | "deviation"
  | "sustained_volatile"
  | "weather_price"
  | "multi_commodity";

export type AlertSeverity = "info" | "warning" | "critical";

export interface Alert {
  id: number;
  tanggal: string;
  region: Region;
  commodity: Commodity;
  alertType: AlertType;
  severity: AlertSeverity;
  judul: string;
  deskripsi: string;
  nilaiAktual: number | null;
  nilaiThreshold: number | null;
  isActive: boolean;
}

export interface Insight {
  id: number;
  tanggal: string;
  tipe: "harian" | "mingguan";
  judul: string;
  konten: string;
  dataSnapshot: Record<string, unknown> | null;
}

// --- API Response Types ---

export interface HeadlineResponse {
  inflasi: {
    mtm: number;
    ytd: number;
    yoy: number;
    ihk: number;
    periode: string;
  };
  topCommodities: {
    commodity: Commodity;
    perubahanMingguan: number;
  }[];
  topRegions: {
    region: Region;
    avgPriceChange: number;
  }[];
  activeAlerts: number;
  latestInsight: Insight | null;
}

export interface PriceTrendResponse {
  commodity: Commodity;
  region: Region;
  data: {
    tanggal: string;
    harga: number;
  }[];
  summary: {
    hargaTerakhir: number;
    perubahanHarian: number;
    perubahanMingguan: number;
    perubahanBulanan: number;
    hargaTertinggi: number;
    hargaTerendah: number;
  };
}

export interface HeatmapResponse {
  data: {
    region: Region;
    avgPriceChange: number;
    riskCategory: "rendah" | "sedang" | "tinggi";
    alertCount: number;
  }[];
}

export interface CommodityRankingResponse {
  data: {
    commodity: Commodity;
    hargaTerakhir: number;
    perubahanHarian: number;
    perubahanMingguan: number;
    perubahanBulanan: number;
  }[];
}

// --- AI Chat Types ---

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  metadata?: {
    sources?: string[];
    periode?: string;
    dataUsed?: Record<string, unknown>;
  };
}

export interface ChatRequest {
  message: string;
  context?: {
    activePage?: string;
    selectedCommodity?: string;
    selectedRegion?: string;
  };
}

export interface ChatResponse {
  message: string;
  metadata: {
    sources: string[];
    periode: string;
    intent: string;
  };
  suggestedQuestions: string[];
}
