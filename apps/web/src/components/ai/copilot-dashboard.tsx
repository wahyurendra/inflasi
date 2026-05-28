"use client";

import { CopilotPopup } from "@copilotkit/react-ui";
import {
  useCopilotReadable,
  useCopilotAction,
  useCopilotAdditionalInstructions,
} from "@copilotkit/react-core";
import { useQuery } from "@tanstack/react-query";
import { usePathname, useRouter } from "next/navigation";
import "@copilotkit/react-ui/styles.css";

const INFLASI_INSTRUCTIONS = `Kamu adalah INFLASI AI — asisten analisis inflasi pangan Indonesia.

KEMAMPUAN:
- Menganalisis data harga komoditas pangan dari PIHPS BI
- Membaca sinyal inflasi (MtM, YtD, YoY) dari BPS
- Mengidentifikasi wilayah & komoditas berisiko
- Menganalisis sinyal global (FAO Index, kurs, harga minyak, supply chain)
- Memprediksi harga komoditas H+7/H+14 menggunakan model forecast
- Menganalisis driver/penyebab inflasi per komoditas
- Mendeteksi anomali harga yang tidak wajar
- Memberikan insight berbasis data yang tersedia di dashboard

ATURAN:
1. Jawab dalam Bahasa Indonesia yang jelas dan ringkas
2. HANYA gunakan data yang tersedia di dashboard. JANGAN mengarang angka.
3. Gunakan format angka Indonesia (titik ribuan, koma desimal). Contoh: Rp 14.850, 5,21%
4. Jika data tidak tersedia, katakan "Data untuk [X] belum tersedia dalam sistem."
5. JANGAN membuat prediksi masa depan atau mengarang penyebab tanpa data pendukung.
6. Jika pertanyaan di luar lingkup inflasi pangan, tolak dengan sopan.
7. Format jawaban dengan paragraf pendek dan bullet points jika perlu.
8. Saat menyebutkan perubahan harga, selalu sertakan arah (naik/turun) dan persentase.`;

export function CopilotDashboard() {
  const pathname = usePathname();
  const router = useRouter();

  useCopilotAdditionalInstructions({ instructions: INFLASI_INSTRUCTIONS });

  // Expose current page context
  useCopilotReadable({
    description: "Halaman dashboard yang sedang dilihat pengguna",
    value: {
      halaman: pathname,
      namaHalaman:
        pathname === "/"
          ? "Overview"
          : pathname === "/komoditas"
            ? "Harga Komoditas"
            : pathname === "/wilayah"
              ? "Peta Wilayah"
              : pathname === "/global"
                ? "Global Signals"
                : pathname === "/alerts"
                  ? "Alert Center"
                  : pathname === "/recommendations"
                    ? "Rekomendasi"
                    : pathname === "/ai"
                      ? "AI Chat"
                      : pathname,
    },
  });

  // Fetch and expose headline inflation data
  const { data: headlineData } = useQuery({
    queryKey: ["headline-inflation"],
    queryFn: () => fetch("/api/inflation/headline").then((r) => r.json()),
  });

  useCopilotReadable({
    description:
      "Data inflasi headline Indonesia terkini: IHK, inflasi MtM (month-to-month), YtD (year-to-date), YoY (year-on-year), dan periode data",
    value: headlineData ?? {
      inflasi: {
        mtm: 0.42,
        ytd: 1.23,
        yoy: 5.21,
        ihk: 118.35,
        periode: "Februari 2026",
      },
      source: "mock",
    },
  });

  // Fetch and expose commodity prices
  const { data: priceData } = useQuery({
    queryKey: ["commodity-prices-copilot"],
    queryFn: () => fetch("/api/prices/daily").then((r) => r.json()),
  });

  useCopilotReadable({
    description:
      "Data harga komoditas pangan harian: beras, cabai rawit, cabai merah, bawang merah, bawang putih, telur ayam, minyak goreng, gula pasir. Termasuk perubahan harian, mingguan, dan bulanan dalam persen.",
    value: priceData ?? [],
  });

  // Fetch and expose alerts
  const { data: alertData } = useQuery({
    queryKey: ["alerts-copilot"],
    queryFn: () => fetch("/api/alerts").then((r) => r.json()),
  });

  useCopilotReadable({
    description:
      "Alert aktif inflasi pangan: peringatan kenaikan harga drastis, volatilitas tinggi, dan anomali wilayah. Severity: critical, warning, info.",
    value: alertData ?? [],
  });

  // Fetch and expose global signals
  const { data: globalData } = useQuery({
    queryKey: ["global-signals-copilot"],
    queryFn: () => fetch("/api/global-signals").then((r) => r.json()),
  });

  useCopilotReadable({
    description:
      "Sinyal pasar global: FAO Food Price Index, harga komoditas global (beras, gandum, CPO, gula, urea, minyak Brent), kurs USD/IDR, dan Supply Chain Pressure Index (GSCPI).",
    value: globalData ?? {},
  });

  // Action: navigate to dashboard page
  useCopilotAction({
    name: "navigasiHalaman",
    description:
      "Navigasi ke halaman dashboard tertentu. Gunakan saat user minta buka/lihat halaman spesifik.",
    parameters: [
      {
        name: "halaman",
        type: "string",
        description:
          "Nama halaman: overview, komoditas, wilayah, global, alerts, recommendations, ai",
        required: true,
      },
    ],
    handler: async ({ halaman }) => {
      const routes: Record<string, string> = {
        overview: "/",
        komoditas: "/komoditas",
        wilayah: "/wilayah",
        global: "/global",
        alerts: "/alerts",
        recommendations: "/recommendations",
        rekomendasi: "/recommendations",
        ai: "/ai",
      };
      const route = routes[halaman.toLowerCase()] || "/";
      router.push(route);
      return `Membuka halaman ${halaman}`;
    },
  });

  // Action: analyze commodity
  useCopilotAction({
    name: "analisisKomoditas",
    description:
      "Analisis mendalam satu komoditas berdasarkan data harga, tren, dan alert aktif. Gunakan data dari readable context.",
    parameters: [
      {
        name: "komoditas",
        type: "string",
        description:
          "Nama komoditas: beras, cabai rawit, cabai merah, bawang merah, bawang putih, telur ayam, minyak goreng, gula pasir",
        required: true,
      },
    ],
    handler: async ({ komoditas }) => {
      const prices = priceData?.data || priceData || [];
      const commodity = Array.isArray(prices)
        ? prices.find(
            (p: { namaDisplay?: string; komoditas?: string }) =>
              (p.namaDisplay || p.komoditas || "")
                .toLowerCase()
                .includes(komoditas.toLowerCase())
          )
        : null;

      if (!commodity) {
        return `Data untuk ${komoditas} tidak ditemukan dalam sistem.`;
      }

      return JSON.stringify({
        komoditas: commodity.namaDisplay || commodity.komoditas || komoditas,
        harga: commodity.harga || commodity.hargaTerakhir,
        perubahanHarian: commodity.perubahanHarian,
        perubahanMingguan: commodity.perubahanMingguan,
        perubahanBulanan: commodity.perubahanBulanan,
      });
    },
  });

  // Action: forecast analysis
  useCopilotAction({
    name: "analisisForecast",
    description:
      "Prediksi harga komoditas H+7 atau H+14. Gunakan saat user bertanya tentang prediksi atau forecast harga.",
    parameters: [
      {
        name: "komoditas",
        type: "string",
        description: "Kode komoditas: CABAI_RAWIT, BERAS, BAWANG_MERAH, TELUR_AYAM, GULA_PASIR, MINYAK_GORENG, BAWANG_PUTIH, CABAI_MERAH",
        required: true,
      },
      {
        name: "horizon",
        type: "number",
        description: "Horizon prediksi dalam hari (7 atau 14). Default: 7",
        required: false,
      },
    ],
    handler: async ({ komoditas, horizon }) => {
      const h = horizon || 7;
      const res = await fetch(`/api/forecast?commodity=${komoditas}&region=00&horizon=${h}`);
      const data = await res.json();

      if (!data?.data?.length) {
        return `Forecast untuk ${komoditas} belum tersedia. Model sedang diproses.`;
      }

      return JSON.stringify({
        komoditas,
        horizon: h,
        dataPoints: data.data.length,
        prediksiTerakhir: data.data[data.data.length - 1],
        modelVersion: data.modelVersion || "v1",
      });
    },
  });

  // Action: driver analysis
  useCopilotAction({
    name: "analisisDriver",
    description:
      "Analisis penyebab/driver perubahan harga komoditas. Gunakan saat user bertanya kenapa harga naik/turun.",
    parameters: [
      {
        name: "komoditas",
        type: "string",
        description: "Kode komoditas: CABAI_RAWIT, BERAS, dll",
        required: true,
      },
    ],
    handler: async ({ komoditas }) => {
      const res = await fetch(`/api/drivers?commodity=${komoditas}&region=00`);
      const data = await res.json();

      if (!data?.drivers?.length) {
        return `Data driver untuk ${komoditas} belum tersedia.`;
      }

      return JSON.stringify({
        komoditas: data.commodity || komoditas,
        tanggal: data.tanggal,
        drivers: data.drivers,
      });
    },
  });

  // Action: anomaly check
  useCopilotAction({
    name: "analisisAnomali",
    description:
      "Cek apakah ada anomali harga hari ini. Gunakan saat user bertanya tentang anomali atau harga tidak wajar.",
    parameters: [],
    handler: async () => {
      const res = await fetch("/api/alerts?severity=critical");
      const data = await res.json();
      const alerts = Array.isArray(data) ? data : data.alerts || [];

      if (alerts.length === 0) {
        return "Tidak ada anomali harga yang terdeteksi saat ini. Semua komoditas dalam batas normal.";
      }

      return JSON.stringify({
        jumlahAnomali: alerts.length,
        anomali: alerts.slice(0, 5).map((a: { judul?: string; severity?: string; komoditas?: string; wilayah?: string }) => ({
          judul: a.judul,
          severity: a.severity,
          komoditas: a.komoditas,
          wilayah: a.wilayah,
        })),
      });
    },
  });

  // Action: compare regions
  useCopilotAction({
    name: "bandingkanWilayah",
    description:
      "Bandingkan tekanan inflasi antar wilayah menggunakan data heatmap regional.",
    parameters: [
      {
        name: "wilayah",
        type: "string",
        description: "Daftar provinsi dipisah koma, contoh: 'Papua, Maluku'",
        required: true,
      },
    ],
    handler: async ({ wilayah }) => {
      const res = await fetch("/api/regions/heatmap");
      const data = await res.json();
      const regions = Array.isArray(data) ? data : data.data || [];

      const names = wilayah.split(",").map((w: string) => w.trim().toLowerCase());
      const matched = regions.filter(
        (r: { namaProvinsi?: string }) =>
          names.some((n: string) =>
            (r.namaProvinsi || "").toLowerCase().includes(n)
          )
      );

      if (matched.length === 0) {
        return `Data untuk wilayah ${wilayah} tidak ditemukan.`;
      }

      return JSON.stringify(matched);
    },
  });

  return (
    <CopilotPopup
      labels={{
        title: "INFLASI AI",
        initial:
          "Halo! Saya INFLASI AI. Tanya apa saja tentang inflasi pangan Indonesia — harga komoditas, tren wilayah, alert, sinyal global, forecast, atau analisis driver.",
        placeholder: "Tanya tentang inflasi pangan...",
      }}
      clickOutsideToClose={false}
    />
  );
}
