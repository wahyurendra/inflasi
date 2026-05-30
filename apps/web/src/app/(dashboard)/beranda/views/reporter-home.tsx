"use client";

import Link from "next/link";
import { CommodityRanking } from "@/components/dashboard/commodity-ranking";
import { useCommodityRanking } from "@/hooks/use-prices";
import { useMyReports } from "@/hooks/use-reports";
import { useLeaderboard } from "@/hooks/use-leaderboard";
import { useAuth } from "@/hooks/use-auth";
import { PlusCircle, Award, Flame, FileText } from "lucide-react";

export function ReporterHome() {
  const { user } = useAuth();
  const { data: myReports } = useMyReports(1);
  const { data: rankingData } = useCommodityRanking("weekly_change", 5);
  const { data: leaderboard } = useLeaderboard("week", 5);

  const totalLaporan = (myReports as { total?: number })?.total ?? 0;
  const approvedCount = ((myReports as { data?: Array<{ status?: string }> })?.data ?? []).filter(
    (r) => r.status === "APPROVED",
  ).length;
  const commodities = (rankingData?.data ?? []).map((c) => ({
    namaDisplay: c.namaDisplay,
    hargaTerakhir: c.hargaTerakhir ?? 0,
    perubahanMingguan: c.perubahanMingguan ?? 0,
    kategori: c.kategori,
  }));
  const board = ((leaderboard as { data?: Array<{ user_name?: string; points?: number; rank?: number }> })?.data ?? []).slice(0, 5);

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">
          Selamat datang{user?.name ? `, ${user.name.split(" ")[0]}` : ""}
        </h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Lapor harga di pasar hari ini untuk membantu pemantauan inflasi.
        </p>
      </div>

      <Link
        href="/lapor"
        className="block bg-gradient-to-br from-primary to-primary/80 text-primary-foreground rounded-md p-5 hover:opacity-95 transition-opacity"
      >
        <div className="flex items-center gap-3">
          <PlusCircle className="h-8 w-8" />
          <div>
            <p className="text-base font-semibold">Lapor Harga Hari Ini</p>
            <p className="text-xs opacity-90 mt-0.5">
              Pilih pasar terdekat, masukkan harga komoditas, dan kirim.
            </p>
          </div>
        </div>
      </Link>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <StatCard icon={FileText} label="Total Laporan" value={totalLaporan} tone="primary" />
        <StatCard icon={Award} label="Disetujui" value={approvedCount} tone="success" />
        <StatCard icon={Flame} label="Streak Minggu Ini" value={"–"} tone="warning" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CommodityRanking
          data={commodities}
          title="Harga Naik Minggu Ini"
        />
        <div className="bg-card rounded-md border p-4">
          <h3 className="text-sm font-semibold mb-3">Top Kontributor Pekan Ini</h3>
          {board.length === 0 ? (
            <p className="text-xs text-muted-foreground">Belum ada data leaderboard.</p>
          ) : (
            <ol className="space-y-1.5">
              {board.map((row, i) => (
                <li key={i} className="flex items-center justify-between text-xs">
                  <span className="text-foreground">
                    #{row.rank ?? i + 1} {row.user_name ?? "—"}
                  </span>
                  <span className="text-primary font-medium">{row.points ?? 0} poin</span>
                </li>
              ))}
            </ol>
          )}
          <Link
            href="/leaderboard"
            className="text-[11px] text-primary mt-3 inline-block hover:underline"
          >
            Lihat leaderboard lengkap →
          </Link>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number | string;
  tone: "primary" | "success" | "warning";
}) {
  const toneClass = {
    primary: "text-primary",
    success: "text-risk-low",
    warning: "text-risk-high",
  }[tone];
  return (
    <div className="bg-card rounded-md border p-4">
      <div className="flex items-center gap-2 text-muted-foreground text-[11px]">
        <Icon className={`h-3.5 w-3.5 ${toneClass}`} />
        <span>{label}</span>
      </div>
      <p className="text-2xl font-semibold mt-1">{value}</p>
    </div>
  );
}
