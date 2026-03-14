import { prisma } from "@/lib/db";

interface ValidationResult {
  confidenceScore: number;
  isAnomaly: boolean;
  deviationPct: number;
  medianPrice: number;
}

export async function validateReport(
  harga: number,
  commodityId: number,
  regionId: number,
  userId: string,
  hasPhotos: boolean
): Promise<ValidationResult> {
  let score = 0;
  let medianPrice = harga;
  let deviationPct = 0;
  let isAnomaly = false;

  try {
    // Get median price for this commodity/region in last 30 days
    const recentPrices = await prisma.factPriceDaily.findMany({
      where: {
        commodityId,
        regionId,
        tanggal: { gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) },
      },
      select: { harga: true },
      orderBy: { harga: "asc" },
    });

    if (recentPrices.length > 0) {
      const prices = recentPrices.map((p) => Number(p.harga));
      const mid = Math.floor(prices.length / 2);
      medianPrice = prices.length % 2 ? prices[mid] : (prices[mid - 1] + prices[mid]) / 2;
      deviationPct = Math.abs((harga - medianPrice) / medianPrice) * 100;

      // Deviation scoring (0-40 points, inversely proportional)
      if (deviationPct <= 5) score += 40;
      else if (deviationPct <= 10) score += 30;
      else if (deviationPct <= 20) score += 20;
      else if (deviationPct <= 30) score += 10;

      isAnomaly = deviationPct > 30;
    } else {
      score += 20; // No comparison data, give moderate score
    }

    // Photo bonus
    if (hasPhotos) score += 15;

    // User reputation (0-25 points)
    const userStats = await prisma.priceReport.groupBy({
      by: ["status"],
      where: { userId },
      _count: true,
    });

    const total = userStats.reduce((sum, s) => sum + s._count, 0);
    const approved = userStats.find((s) => s.status === "APPROVED")?._count || 0;

    if (total >= 5) {
      const approvalRate = approved / total;
      score += Math.round(approvalRate * 25);
    } else {
      score += 10; // New user gets moderate reputation score
    }

    // Similar reports bonus (+10 if others reported for same commodity/region/date)
    const similarCount = await prisma.priceReport.count({
      where: {
        commodityId,
        regionId,
        userId: { not: userId },
        tanggal: { gte: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000) },
      },
    });
    if (similarCount > 0) score += 10;

    // Reasonable price range (+10)
    if (harga >= 500 && harga <= 500000) score += 10;
  } catch {
    // DB not available, return default scores
    score = hasPhotos ? 65 : 50;
  }

  return {
    confidenceScore: Math.min(100, Math.max(0, score)),
    isAnomaly,
    deviationPct: Math.round(deviationPct * 100) / 100,
    medianPrice,
  };
}

export async function detectDuplicate(
  userId: string,
  commodityId: number,
  namaPasar: string,
  tanggal: string
): Promise<boolean> {
  try {
    const existing = await prisma.priceReport.findFirst({
      where: {
        userId,
        commodityId,
        namaPasar,
        tanggal: new Date(tanggal),
      },
    });
    return !!existing;
  } catch {
    return false;
  }
}
