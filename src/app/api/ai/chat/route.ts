import { NextRequest, NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { prisma } from "@/lib/db";

const anthropic = new Anthropic();

const SYSTEM_PROMPT = `Kamu adalah asisten analisis inflasi pangan Indonesia bernama INFLASI AI.
Tugasmu menjawab pertanyaan HANYA berdasarkan data yang diberikan dalam tag <data>.

ATURAN KETAT:
1. HANYA gunakan data yang ada di tag <data>. JANGAN mengarang angka.
2. SELALU sebutkan periode data dan sumber di akhir jawaban.
3. Jika data tidak tersedia, katakan "Data untuk [X] belum tersedia dalam sistem."
4. JANGAN membuat prediksi masa depan.
5. JANGAN mengarang penyebab tanpa indikator pendukung dari data.
6. Jawab dalam Bahasa Indonesia yang jelas dan ringkas.
7. Gunakan format angka Indonesia (titik untuk ribuan, koma untuk desimal).
8. Jika user bertanya di luar lingkup inflasi pangan, tolak dengan sopan.
9. Format jawaban dengan paragraf pendek yang mudah dibaca.
10. Saat menyebutkan perubahan harga, selalu sertakan arah (naik/turun) dan persentase.`;

interface ChatRequest {
  message: string;
  context?: {
    activePage?: string;
    selectedCommodity?: string;
    selectedRegion?: string;
  };
}

async function gatherDashboardData() {
  // Get latest prices for all commodities (national average)
  const latestDate = await prisma.factPriceDaily.findFirst({
    orderBy: { tanggal: "desc" },
    select: { tanggal: true },
  });

  if (!latestDate) {
    return null;
  }

  const prices = await prisma.factPriceDaily.findMany({
    where: { tanggal: latestDate.tanggal },
    include: { commodity: true, region: true },
    orderBy: { commodity: { namaDisplay: "asc" } },
  });

  const alerts = await prisma.analyticsAlert.findMany({
    where: { isActive: true },
    include: { commodity: true, region: true },
    orderBy: [{ severity: "asc" }, { tanggal: "desc" }],
    take: 10,
  });

  const latestInsight = await prisma.analyticsInsight.findFirst({
    orderBy: { tanggal: "desc" },
  });

  // Get forecasts
  const forecasts = await prisma.analyticsForecast.findMany({
    where: { tanggal: { gte: new Date() }, horizon: 14 },
    include: { commodity: true, region: true },
    orderBy: { tanggal: "asc" },
    take: 20,
  }).catch(() => []);

  // Get risk scores
  const riskScores = await prisma.analyticsRiskScore.findMany({
    where: { tanggal: latestDate.tanggal },
    include: { commodity: true, region: true },
    orderBy: { riskScoreTotal: "desc" },
    take: 10,
  }).catch(() => []);

  // Get global signals
  const latestKurs = await prisma.extExchangeRate.findFirst({
    orderBy: { tanggal: "desc" },
  }).catch(() => null);

  return {
    tanggalData: latestDate.tanggal.toISOString().slice(0, 10),
    hargaKomoditas: prices.map((p) => ({
      komoditas: p.commodity.namaDisplay,
      wilayah: p.region.namaProvinsi,
      harga: Number(p.harga),
      perubahanHarian: p.perubahanHarian ? Number(p.perubahanHarian) : null,
      perubahanMingguan: p.perubahanMingguan ? Number(p.perubahanMingguan) : null,
      perubahanBulanan: p.perubahanBulanan ? Number(p.perubahanBulanan) : null,
    })),
    alertAktif: alerts.map((a) => ({
      severity: a.severity,
      judul: a.judul,
      deskripsi: a.deskripsi,
      komoditas: a.commodity.namaDisplay,
      wilayah: a.region.namaProvinsi,
    })),
    insightTerakhir: latestInsight
      ? { judul: latestInsight.judul, konten: latestInsight.konten }
      : null,
    forecastRingkasan: forecasts.length > 0
      ? forecasts.slice(0, 8).map((f) => ({
          komoditas: f.commodity.namaDisplay,
          wilayah: f.region.namaProvinsi,
          tanggal: f.tanggal.toISOString().slice(0, 10),
          prediksi: Number(f.yhat),
          batasAtas: Number(f.yhatUpper),
          batasBawah: Number(f.yhatLower),
        }))
      : null,
    riskTertinggi: riskScores.length > 0
      ? riskScores.slice(0, 5).map((r) => ({
          komoditas: r.commodity.namaDisplay,
          wilayah: r.region.namaProvinsi,
          skor: Number(r.riskScoreTotal),
          kategori: r.riskCategory,
        }))
      : null,
    kursUsdIdr: latestKurs
      ? { kurs: Number(latestKurs.kursTengah), tanggal: latestKurs.tanggal.toISOString().slice(0, 10) }
      : null,
  };
}

export async function POST(request: NextRequest) {
  try {
    const body: ChatRequest = await request.json();

    if (!body.message?.trim()) {
      return NextResponse.json(
        { error: "Message is required" },
        { status: 400 }
      );
    }

    // Gather data from database
    const dashboardData = await gatherDashboardData();
    const tanggalData = dashboardData?.tanggalData ?? "N/A";

    const dataContext = dashboardData
      ? JSON.stringify(dashboardData, null, 2)
      : '{"message": "Database belum memiliki data. Jalankan ETL pipeline terlebih dahulu."}';

    const userPrompt = `Pertanyaan user: ${body.message}

<data>
${dataContext}
</data>

<metadata>
Sumber: PIHPS BI, BPS
Tanggal data: ${tanggalData}
${!dashboardData ? "Catatan: Database belum memiliki data. Informasikan user untuk menjalankan ETL pipeline." : ""}
</metadata>

Jawab pertanyaan user berdasarkan data di atas. Sertakan angka spesifik dan periode. Format jawabanmu agar ringkas dan mudah dibaca.`;

    const response = await anthropic.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1024,
      system: SYSTEM_PROMPT,
      messages: [{ role: "user", content: userPrompt }],
    });

    const assistantMessage =
      response.content[0].type === "text" ? response.content[0].text : "";

    // Generate suggested follow-up questions
    const suggestedQuestions = generateSuggestions(body.message);

    return NextResponse.json({
      message: assistantMessage,
      metadata: {
        sources: ["PIHPS BI", "BPS"],
        periode: tanggalData,
        intent: "general",
      },
      suggestedQuestions,
    });
  } catch (error) {
    console.error("AI Chat error:", error);

    // If API key is missing, return helpful message
    if (error instanceof Error && error.message.includes("API key")) {
      return NextResponse.json({
        message:
          "AI Assistant belum dikonfigurasi. Silakan set ANTHROPIC_API_KEY di file .env.local untuk mengaktifkan fitur ini.",
        metadata: { sources: [], periode: "", intent: "error" },
        suggestedQuestions: [],
      });
    }

    return NextResponse.json(
      { error: "Failed to process chat request" },
      { status: 500 }
    );
  }
}

function generateSuggestions(
  currentQuestion: string,
): string[] {
  const suggestions = [
    "Komoditas apa yang paling naik minggu ini?",
    "Wilayah mana yang perlu diwaspadai?",
    "Bagaimana tren harga beras bulan ini?",
    "Jelaskan alert yang sedang aktif",
    "Bandingkan harga cabai rawit dan cabai merah",
    "Kenapa bawang merah volatilitasnya tinggi?",
    "Rangkum kondisi inflasi pangan hari ini",
    "Komoditas mana yang harganya turun?",
  ];

  // Filter out the current question and return 3-4 suggestions
  return suggestions
    .filter((s) => s.toLowerCase() !== currentQuestion.toLowerCase())
    .slice(0, 4);
}
