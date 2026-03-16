// TODO: This entire gamification module should be migrated to the FastAPI backend.
// The points/badge logic should run server-side in the reports endpoint after a report
// is approved. For now, the Prisma calls are replaced with apiClient calls for data access,
// but the full logic should eventually live in FastAPI as a single /gamification/award-points endpoint.

import { apiClient } from "@/lib/api-client";
import { notifyBadgeEarned } from "@/lib/notifications";

const BADGE_DEFINITIONS = [
  { code: "REPORTER_PEMULA", name: "Reporter Pemula", threshold: 5, category: "reports", icon: "Award" },
  { code: "REPORTER_AKTIF", name: "Reporter Aktif", threshold: 25, category: "reports", icon: "Star" },
  { code: "REPORTER_VETERAN", name: "Reporter Veteran", threshold: 100, category: "reports", icon: "Crown" },
  { code: "STREAK_7", name: "Streak 7 Hari", threshold: 7, category: "streak", icon: "Flame" },
  { code: "STREAK_30", name: "Streak 30 Hari", threshold: 30, category: "streak", icon: "Zap" },
  { code: "AKURASI_TINGGI", name: "Akurasi Tinggi", threshold: 90, category: "accuracy", icon: "Target" },
];

interface UserPoints {
  userId: string;
  totalPoints: number;
  monthlyPoints: number;
  totalReports: number;
  approvedReports: number;
  currentStreak: number;
  longestStreak: number;
  lastReportDate: string | null;
}

interface UserBadge {
  badge: { code: string };
}

export async function awardPoints(
  userId: string,
  hasPhotos: boolean = false
): Promise<{ points: number; newBadges: string[] }> {
  const newBadges: string[] = [];
  const basePoints = 10;
  const photoBonus = hasPhotos ? 5 : 0;

  try {
    // Upsert user points via API
    const userPoints = await apiClient.post<UserPoints>("/gamification/upsert-points", {
      userId,
      pointsToAdd: basePoints + photoBonus,
      incrementReports: true,
    });

    // Update streak
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const lastReport = userPoints.lastReportDate
      ? new Date(userPoints.lastReportDate)
      : null;

    let newStreak = userPoints.currentStreak;
    if (lastReport) {
      lastReport.setHours(0, 0, 0, 0);
      const diffDays = Math.floor(
        (today.getTime() - lastReport.getTime()) / (1000 * 60 * 60 * 24)
      );
      if (diffDays === 1) {
        newStreak += 1;
        // Streak bonus
        await apiClient.post("/gamification/upsert-points", {
          userId,
          pointsToAdd: 2,
          incrementReports: false,
        });
      } else if (diffDays > 1) {
        newStreak = 1;
      }
    } else {
      newStreak = 1;
    }

    await apiClient.patch("/gamification/update-streak", {
      userId,
      currentStreak: newStreak,
      longestStreak: Math.max(newStreak, userPoints.longestStreak),
      lastReportDate: today.toISOString(),
    });

    // Check badges
    const existing = await apiClient.get<UserBadge[]>(
      "/gamification/user-badges",
      { userId }
    );
    const existingCodes = new Set(existing.map((b) => b.badge.code));

    // Re-fetch updated points
    const updated = await apiClient.get<UserPoints>(
      "/gamification/user-points",
      { userId }
    );

    for (const def of BADGE_DEFINITIONS) {
      if (existingCodes.has(def.code)) continue;

      let earned = false;

      if (def.category === "reports" && updated.approvedReports >= def.threshold) {
        earned = true;
      } else if (def.category === "streak" && updated.currentStreak >= def.threshold) {
        earned = true;
      } else if (
        def.category === "accuracy" &&
        updated.totalReports >= 20 &&
        (updated.approvedReports / updated.totalReports) * 100 >= def.threshold
      ) {
        earned = true;
      }

      if (earned) {
        await apiClient.post("/gamification/award-badge", {
          userId,
          badgeCode: def.code,
          badgeName: def.name,
          badgeDescription: `Diperoleh setelah ${def.threshold} ${def.category === "reports" ? "laporan disetujui" : def.category === "streak" ? "hari berturut-turut" : "% akurasi"}`,
          badgeIcon: def.icon,
          badgeThreshold: def.threshold,
          badgeCategory: def.category,
        });
        newBadges.push(def.name);
        await notifyBadgeEarned(userId, def.name);
      }
    }

    return { points: basePoints + photoBonus, newBadges };
  } catch {
    return { points: 0, newBadges: [] };
  }
}

export { BADGE_DEFINITIONS };
