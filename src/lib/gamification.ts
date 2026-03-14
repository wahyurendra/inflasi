import { prisma } from "@/lib/db";
import { notifyBadgeEarned } from "@/lib/notifications";

const BADGE_DEFINITIONS = [
  { code: "REPORTER_PEMULA", name: "Reporter Pemula", threshold: 5, category: "reports", icon: "Award" },
  { code: "REPORTER_AKTIF", name: "Reporter Aktif", threshold: 25, category: "reports", icon: "Star" },
  { code: "REPORTER_VETERAN", name: "Reporter Veteran", threshold: 100, category: "reports", icon: "Crown" },
  { code: "STREAK_7", name: "Streak 7 Hari", threshold: 7, category: "streak", icon: "Flame" },
  { code: "STREAK_30", name: "Streak 30 Hari", threshold: 30, category: "streak", icon: "Zap" },
  { code: "AKURASI_TINGGI", name: "Akurasi Tinggi", threshold: 90, category: "accuracy", icon: "Target" },
];

export async function awardPoints(
  userId: string,
  hasPhotos: boolean = false
): Promise<{ points: number; newBadges: string[] }> {
  const newBadges: string[] = [];
  const basePoints = 10;
  const photoBonus = hasPhotos ? 5 : 0;

  try {
    const userPoints = await prisma.userPoints.upsert({
      where: { userId },
      update: {
        totalPoints: { increment: basePoints + photoBonus },
        monthlyPoints: { increment: basePoints + photoBonus },
        totalReports: { increment: 1 },
        approvedReports: { increment: 1 },
      },
      create: {
        userId,
        totalPoints: basePoints + photoBonus,
        monthlyPoints: basePoints + photoBonus,
        totalReports: 1,
        approvedReports: 1,
      },
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
        await prisma.userPoints.update({
          where: { userId },
          data: {
            totalPoints: { increment: 2 },
            monthlyPoints: { increment: 2 },
          },
        });
      } else if (diffDays > 1) {
        newStreak = 1;
      }
    } else {
      newStreak = 1;
    }

    await prisma.userPoints.update({
      where: { userId },
      data: {
        currentStreak: newStreak,
        longestStreak: Math.max(newStreak, userPoints.longestStreak),
        lastReportDate: today,
      },
    });

    // Check badges
    const existing = await prisma.userBadge.findMany({
      where: { userId },
      select: { badge: { select: { code: true } } },
    });
    const existingCodes = new Set(existing.map((b) => b.badge.code));

    for (const def of BADGE_DEFINITIONS) {
      if (existingCodes.has(def.code)) continue;

      let earned = false;
      const updated = await prisma.userPoints.findUnique({ where: { userId } });
      if (!updated) continue;

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
        let badge = await prisma.badge.findUnique({ where: { code: def.code } });
        if (!badge) {
          badge = await prisma.badge.create({
            data: {
              code: def.code,
              name: def.name,
              description: `Diperoleh setelah ${def.threshold} ${def.category === "reports" ? "laporan disetujui" : def.category === "streak" ? "hari berturut-turut" : "% akurasi"}`,
              icon: def.icon,
              threshold: def.threshold,
              category: def.category,
            },
          });
        }

        await prisma.userBadge.create({
          data: { userId, badgeId: badge.id },
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
