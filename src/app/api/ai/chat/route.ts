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
  };
}

// Mock data used when database is empty
const MOCK_DATA = {
  tanggalData: "2026-03-10",
  hargaKomoditas: [
    { komoditas: "Beras", wilayah: "Nasional", harga: 14850, perubahanHarian: 0.3, perubahanMingguan: 1.2, perubahanBulanan: 3.8 },
    { komoditas: "Cabai Rawit", wilayah: "Nasional", harga: 85000, perubahanHarian: 2.1, perubahanMingguan: 12.0, perubahanBulanan: 18.5 },
    { komoditas: "Cabai Merah", wilayah: "Nasional", harga: 55000, perubahanHarian: -0.5, perubahanMingguan: -1.2, perubahanBulanan: 5.3 },
    { komoditas: "Bawang Merah", wilayah: "Nasional", harga: 42000, perubahanHarian: 0.5, perubahanMingguan: 7.0, perubahanBulanan: 11.2 },
    { komoditas: "Bawang Putih", wilayah: "Nasional", harga: 38000, perubahanHarian: 0.0, perubahanMingguan: -0.3, perubahanBulanan: 2.1 },
    { komoditas: "Telur Ayam", wilayah: "Nasional", harga: 28500, perubahanHarian: 0.8, perubahanMingguan: 4.0, perubahanBulanan: 6.1 },
    { komoditas: "Minyak Goreng", wilayah: "Nasional", harga: 18100, perubahanHarian: -0.1, perubahanMingguan: 0.5, perubahanBulanan: 1.2 },
    { komoditas: "Gula Pasir", wilayah: "Nasional", harga: 17200, perubahanHarian: 0.2, perubahanMingguan: 2.0, perubahanBulanan: 3.5 },
  ],
  alertAktif: [
    { severity: "critical", judul: "Cabai rawit: spike +12% / 7 hari", deskripsi: "Harga cabai rawit naik 12% dalam 7 hari di Jawa Barat, Jawa Timur, Jawa Tengah, Sumatera Utara, Lampung.", komoditas: "Cabai Rawit", wilayah: "Nasional" },
    { severity: "warning", judul: "Bawang merah: volatilitas tinggi 2 minggu", deskripsi: "Bawang merah CV 18.3% selama 14 hari (threshold 15%).", komoditas: "Bawang Merah", wilayah: "Nasional" },
    { severity: "critical", judul: "Papua: 3 komoditas naik >5% bersamaan", deskripsi: "Di Papua, beras +5%, telur +7%, gula +4% dalam 7 hari.", komoditas: "Multi", wilayah: "Papua" },
  ],
  inflasi: { mtm: 0.42, ytd: 1.23, yoy: 5.21, ihk: 118.35, periode: "Februari 2026" },
  insightTerakhir: null,
};

export async function POST(request: NextRequest) {
  try {
    const body: ChatRequest = await request.json();

    if (!body.message?.trim()) {
      return NextResponse.json(
        { error: "Message is required" },
        { status: 400 }
      );
    }

    // Gather data from database or use mock
    let dashboardData = await gatherDashboardData();
    const usingMock = !dashboardData;
    if (!dashboardData) {
      dashboardData = MOCK_DATA;
    }

    const dataContext = JSON.stringify(dashboardData, null, 2);

    const userPrompt = `Pertanyaan user: ${body.message}

<data>
${dataContext}
</data>

<metadata>
Sumber: PIHPS BI, BPS
Tanggal data: ${dashboardData.tanggalData}
${usingMock ? "Catatan: Menggunakan data contoh karena database belum terisi." : ""}
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
    const suggestedQuestions = generateSuggestions(body.message, dashboardData);

    return NextResponse.json({
      message: assistantMessage,
      metadata: {
        sources: ["PIHPS BI", "BPS"],
        periode: dashboardData.tanggalData,
        intent: "general",
        usingMockData: usingMock,
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
  _data: Record<string, unknown>
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
