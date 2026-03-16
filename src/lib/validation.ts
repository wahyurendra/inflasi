import { apiClient } from "@/lib/api-client";

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
  try {
    const result = await apiClient.post<ValidationResult>("/reports/validate", {
      harga,
      commodityId,
      regionId,
      userId,
      hasPhotos,
    });
    return result;
  } catch {
    // API not available, return default scores
    const score = hasPhotos ? 65 : 50;
    return {
      confidenceScore: score,
      isAnomaly: false,
      deviationPct: 0,
      medianPrice: harga,
    };
  }
}

export async function detectDuplicate(
  userId: string,
  commodityId: number,
  namaPasar: string,
  tanggal: string
): Promise<boolean> {
  try {
    const result = await apiClient.post<{ isDuplicate: boolean }>("/reports/detect-duplicate", {
      userId,
      commodityId,
      namaPasar,
      tanggal,
    });
    return result.isDuplicate;
  } catch {
    return false;
  }
}
