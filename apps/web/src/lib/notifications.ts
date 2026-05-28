import { apiClient } from "@/lib/api-client";

export async function createNotification(
  userId: string,
  type: string,
  title: string,
  message: string,
  data?: Record<string, unknown>
) {
  try {
    return await apiClient.post("/notifications/", {
      userId,
      type,
      title,
      message,
      data: data ?? undefined,
    });
  } catch {
    console.error("Failed to create notification");
    return null;
  }
}

export async function notifyReportSubmitted(userId: string, commodityName: string) {
  return createNotification(
    userId,
    "report_received",
    "Laporan Diterima",
    `Laporan harga ${commodityName} Anda telah diterima dan sedang ditinjau.`
  );
}

export async function notifyReportApproved(
  userId: string,
  commodityName: string,
  reportId: string
) {
  return createNotification(
    userId,
    "report_approved",
    "Laporan Disetujui",
    `Laporan harga ${commodityName} Anda telah disetujui. Terima kasih atas kontribusi Anda!`,
    { reportId }
  );
}

export async function notifyReportRejected(
  userId: string,
  commodityName: string,
  reason?: string
) {
  return createNotification(
    userId,
    "report_rejected",
    "Laporan Ditolak",
    `Laporan harga ${commodityName} Anda ditolak.${reason ? ` Alasan: ${reason}` : ""}`,
  );
}

export async function notifyBadgeEarned(userId: string, badgeName: string) {
  return createNotification(
    userId,
    "badge_earned",
    "Badge Baru!",
    `Selamat! Anda mendapatkan badge "${badgeName}".`
  );
}
