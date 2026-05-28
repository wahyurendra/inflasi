"use client";

import { CopilotChat } from "@copilotkit/react-ui";
import {
  useCopilotChatSuggestions,
  useCopilotReadable,
  useCopilotAction,
} from "@copilotkit/react-core";
import { useQuery } from "@tanstack/react-query";
import "@copilotkit/react-ui/styles.css";

function AIAgentContext() {
  // Fetch real-time data for the agent
  const { data: priceData } = useQuery({
    queryKey: ["ai-agent-prices"],
    queryFn: () => fetch("/api/prices/daily").then((r) => r.json()),
  });

  const { data: alertData } = useQuery({
    queryKey: ["ai-agent-alerts"],
    queryFn: () => fetch("/api/alerts").then((r) => r.json()),
  });

  const { data: globalData } = useQuery({
    queryKey: ["ai-agent-global"],
    queryFn: () => fetch("/api/global-signals").then((r) => r.json()),
  });

  // Feed context to the agent
  useCopilotReadable({
    description:
      "Data harga komoditas pangan terkini: beras, cabai rawit, cabai merah, bawang merah, bawang putih, telur ayam, minyak goreng, gula pasir. Termasuk perubahan harian, mingguan, dan bulanan.",
    value: priceData ?? [],
  });

  useCopilotReadable({
    description: "Alert aktif inflasi pangan: severity critical/warning/info.",
    value: alertData ?? [],
  });

  useCopilotReadable({
    description:
      "Sinyal global: FAO Food Price Index, harga komoditas global, kurs USD/IDR, GSCPI.",
    value: globalData ?? {},
  });

  // Agent actions — forecast
  useCopilotAction({
    name: "analisisForecast",
    description:
      "Prediksi harga komoditas H+7 atau H+14. Gunakan saat user bertanya tentang prediksi atau forecast harga.",
    parameters: [
      {
        name: "komoditas",
        type: "string",
        description:
          "Kode komoditas: CABAI_RAWIT, BERAS, BAWANG_MERAH, TELUR_AYAM, GULA_PASIR, MINYAK_GORENG, BAWANG_PUTIH, CABAI_MERAH",
        required: true,
      },
      {
        name: "horizon",
        type: "number",
        description: "Horizon prediksi: 7 atau 14 hari",
        required: false,
      },
    ],
    handler: async ({ komoditas, horizon }) => {
      const h = horizon || 7;
      const res = await fetch(
        `/api/forecast?commodity=${komoditas}&region=00&horizon=${h}`
      );
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

  // Agent actions — driver analysis
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
      const res = await fetch(
        `/api/drivers?commodity=${komoditas}&region=00`
      );
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

  // Agent actions — anomaly detection
  useCopilotAction({
    name: "analisisAnomali",
    description:
      "Cek anomali harga hari ini. Gunakan saat user bertanya tentang anomali atau harga tidak wajar.",
    parameters: [],
    handler: async () => {
      const res = await fetch("/api/alerts?severity=critical");
      const data = await res.json();
      const alerts = Array.isArray(data) ? data : data.alerts || [];
      if (alerts.length === 0) {
        return "Tidak ada anomali harga yang terdeteksi saat ini.";
      }
      return JSON.stringify({
        jumlahAnomali: alerts.length,
        anomali: alerts.slice(0, 5),
      });
    },
  });

  // Agent actions — RAG search
  useCopilotAction({
    name: "cariData",
    description:
      "Cari data spesifik di database. Gunakan saat user bertanya detail yang tidak ada di context.",
    parameters: [
      {
        name: "query",
        type: "string",
        description: "Query pencarian, e.g. 'harga beras jawa timur'",
        required: true,
      },
    ],
    handler: async ({ query }) => {
      const res = await fetch("/api/ai/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      return JSON.stringify(data);
    },
  });

  // Chat suggestions
  useCopilotChatSuggestions({
    instructions:
      "Berikan 3 saran pertanyaan dalam Bahasa Indonesia tentang inflasi pangan: harga komoditas, forecast, driver, anomali, atau perbandingan wilayah.",
    maxSuggestions: 3,
  });

  return null;
}

export default function AIPage() {
  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="mb-4">
        <h2 className="text-lg font-bold text-foreground">AI Assistant</h2>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Agent AI untuk analisis inflasi pangan — forecast, driver, anomali,
          dan rekomendasi
        </p>
      </div>

      <div className="flex-1 rounded-xl border bg-card overflow-hidden">
        <AIAgentContext />
        <CopilotChat
          className="h-full"
          labels={{
            title: "INFLASI AI Agent",
            initial:
              "Halo! Saya INFLASI AI Agent. Saya bisa membantu:\n\n• **Forecast** — Prediksi harga komoditas H+7/H+14\n• **Driver Analysis** — Kenapa harga naik/turun?\n• **Anomali** — Deteksi harga tidak wajar\n• **Data Search** — Cari data harga, wilayah, alert\n\nSilakan tanya apa saja tentang inflasi pangan Indonesia.",
            placeholder: "Tanya tentang inflasi pangan...",
          }}
          instructions="Kamu adalah INFLASI AI Agent — asisten analisis inflasi pangan Indonesia. Jawab dalam Bahasa Indonesia. HANYA gunakan data dari context dan hasil action. JANGAN mengarang angka. Gunakan format angka Indonesia (titik ribuan, koma desimal). Jika data tidak tersedia, katakan dengan jelas. Gunakan action yang tersedia (analisisForecast, analisisDriver, analisisAnomali, cariData) untuk mengambil data yang dibutuhkan."
        />
      </div>
    </div>
  );
}
