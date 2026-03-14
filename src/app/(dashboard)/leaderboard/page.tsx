"use client";

import { useState } from "react";
import { useLeaderboard } from "@/hooks/use-leaderboard";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Trophy, Medal, Award, Flame } from "lucide-react";

export default function LeaderboardPage() {
  const [period, setPeriod] = useState("all");
  const { data, isLoading } = useLeaderboard(period);

  const leaders = data?.data || [];

  const getRankIcon = (rank: number) => {
    if (rank === 1) return <Trophy className="h-5 w-5 text-yellow-500" />;
    if (rank === 2) return <Medal className="h-5 w-5 text-gray-400" />;
    if (rank === 3) return <Medal className="h-5 w-5 text-amber-600" />;
    return <span className="w-5 text-center text-sm font-bold text-muted-foreground">{rank}</span>;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-bold text-foreground flex items-center gap-2">
          <Trophy className="h-5 w-5 text-primary" />
          Leaderboard Reporter
        </h1>
        <p className="text-sm text-muted-foreground">
          Kontributor laporan harga terbaik
        </p>
      </div>

      <Tabs value={period} onValueChange={setPeriod}>
        <TabsList>
          <TabsTrigger value="all">Semua Waktu</TabsTrigger>
          <TabsTrigger value="month">Bulan Ini</TabsTrigger>
        </TabsList>
      </Tabs>

      {isLoading ? (
        <div className="text-center py-12 text-muted-foreground">Memuat...</div>
      ) : (
        <div className="bg-card rounded-xl border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-center p-3 w-16 font-medium text-muted-foreground">Rank</th>
                  <th className="text-left p-3 font-medium text-muted-foreground">Nama</th>
                  <th className="text-left p-3 font-medium text-muted-foreground">Provinsi</th>
                  <th className="text-right p-3 font-medium text-muted-foreground">Poin</th>
                  <th className="text-right p-3 font-medium text-muted-foreground">Laporan</th>
                  <th className="text-right p-3 font-medium text-muted-foreground">Badge</th>
                </tr>
              </thead>
              <tbody>
                {leaders.map((leader: Record<string, unknown>) => (
                  <tr
                    key={leader.rank as number}
                    className={`border-b last:border-0 transition-colors ${
                      (leader.rank as number) <= 3
                        ? "bg-primary/5"
                        : "hover:bg-muted/30"
                    }`}
                  >
                    <td className="p-3 text-center">
                      <div className="flex items-center justify-center">
                        {getRankIcon(leader.rank as number)}
                      </div>
                    </td>
                    <td className="p-3">
                      <div className="font-medium">{leader.name as string}</div>
                      {(leader.streak as number) >= 3 && (
                        <div className="flex items-center gap-1 text-xs text-orange-500 mt-0.5">
                          <Flame className="h-3 w-3" />
                          {leader.streak as number} hari streak
                        </div>
                      )}
                    </td>
                    <td className="p-3 text-muted-foreground">{leader.province as string}</td>
                    <td className="p-3 text-right font-bold text-primary">
                      {(leader.points as number).toLocaleString()}
                    </td>
                    <td className="p-3 text-right">{leader.reports as number}</td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Award className="h-3.5 w-3.5 text-muted-foreground" />
                        {leader.badges as number}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
