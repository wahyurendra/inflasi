"use client";

import { useCrossRegionComparison, useVolatilityRanking, usePriceGap } from "@/hooks/use-intelligence";
import { BarChart3, ArrowUpDown, TrendingUp, TrendingDown } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

export default function IntelligencePage() {
  const { data: comparisonData } = useCrossRegionComparison();
  const { data: volatilityData } = useVolatilityRanking();
  const { data: priceGapData } = usePriceGap();

  const comparison = comparisonData?.data || [];
  const volatility = volatilityData?.data || [];
  const priceGaps = priceGapData?.data || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-bold text-foreground flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          Price Intelligence
        </h1>
        <p className="text-sm text-muted-foreground">
          Analisis perbandingan harga, volatilitas, dan price gap antar wilayah
        </p>
      </div>

      {/* Volatility Ranking */}
      <div className="bg-card rounded-xl border p-5">
        <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
          <ArrowUpDown className="h-4 w-4" />
          Volatilitas Komoditas (CV 14 Hari)
        </h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={volatility} layout="vertical" margin={{ left: 80 }}>
              <XAxis type="number" tickFormatter={(v) => `${v}%`} />
              <YAxis type="category" dataKey="commodity" tick={{ fontSize: 12 }} width={80} />
              <Tooltip formatter={(value) => [`${value}%`, "CV"]} />
              <Bar dataKey="cv" radius={[0, 4, 4, 0]}>
                {volatility.map((entry: Record<string, unknown>, i: number) => (
                  <Cell
                    key={i}
                    fill={
                      (entry.cv as number) > 15
                        ? "#ef4444"
                        : (entry.cv as number) > 8
                        ? "#f97316"
                        : "#22c55e"
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Price Gap Analysis */}
      <div className="bg-card rounded-xl border p-5">
        <h2 className="text-sm font-semibold mb-4">Price Gap Antar Wilayah</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2 font-medium text-muted-foreground">Komoditas</th>
                <th className="text-right p-2 font-medium text-muted-foreground">Terendah</th>
                <th className="text-left p-2 font-medium text-muted-foreground">Wilayah</th>
                <th className="text-right p-2 font-medium text-muted-foreground">Tertinggi</th>
                <th className="text-left p-2 font-medium text-muted-foreground">Wilayah</th>
                <th className="text-right p-2 font-medium text-muted-foreground">Gap</th>
                <th className="text-right p-2 font-medium text-muted-foreground">Gap %</th>
              </tr>
            </thead>
            <tbody>
              {priceGaps.map((item: Record<string, unknown>, i: number) => (
                <tr key={i} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="p-2 font-medium">{item.commodity as string}</td>
                  <td className="p-2 text-right text-green-600 font-mono">
                    Rp {(item.lowest as number).toLocaleString("id-ID")}
                  </td>
                  <td className="p-2 text-muted-foreground text-xs">{item.lowRegion as string}</td>
                  <td className="p-2 text-right text-red-600 font-mono">
                    Rp {(item.highest as number).toLocaleString("id-ID")}
                  </td>
                  <td className="p-2 text-muted-foreground text-xs">{item.highRegion as string}</td>
                  <td className="p-2 text-right font-mono">
                    Rp {(item.gap as number).toLocaleString("id-ID")}
                  </td>
                  <td className="p-2 text-right">
                    <span
                      className={`font-bold ${
                        (item.gapPct as number) > 50
                          ? "text-red-600"
                          : (item.gapPct as number) > 25
                          ? "text-orange-600"
                          : "text-green-600"
                      }`}
                    >
                      {item.gapPct as number}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cross-Region Comparison */}
      <div className="bg-card rounded-xl border p-5">
        <h2 className="text-sm font-semibold mb-4">Perbandingan Harga Antar Wilayah</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2 font-medium text-muted-foreground">Wilayah</th>
                <th className="text-right p-2 font-medium text-muted-foreground">Beras</th>
                <th className="text-right p-2 font-medium text-muted-foreground">Cabai Merah</th>
                <th className="text-right p-2 font-medium text-muted-foreground">Cabai Rawit</th>
                <th className="text-right p-2 font-medium text-muted-foreground">Bawang Merah</th>
                <th className="text-right p-2 font-medium text-muted-foreground">Telur Ayam</th>
              </tr>
            </thead>
            <tbody>
              {comparison.map((item: Record<string, unknown>, i: number) => (
                <tr key={i} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="p-2 font-medium">{item.region as string}</td>
                  <td className="p-2 text-right font-mono">
                    {(item.beras as number)?.toLocaleString("id-ID") || "-"}
                  </td>
                  <td className="p-2 text-right font-mono">
                    {(item.cabaiMerah as number)?.toLocaleString("id-ID") || "-"}
                  </td>
                  <td className="p-2 text-right font-mono">
                    {(item.cabaiRawit as number)?.toLocaleString("id-ID") || "-"}
                  </td>
                  <td className="p-2 text-right font-mono">
                    {(item.bawangMerah as number)?.toLocaleString("id-ID") || "-"}
                  </td>
                  <td className="p-2 text-right font-mono">
                    {(item.telurAyam as number)?.toLocaleString("id-ID") || "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <TrendingUp className="h-4 w-4 text-red-500" />
            Paling Volatil
          </div>
          <p className="font-bold">{volatility[0]?.commodity || "-"}</p>
          <p className="text-sm text-red-600">CV {volatility[0]?.cv || 0}%</p>
        </div>
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <ArrowUpDown className="h-4 w-4 text-orange-500" />
            Price Gap Terbesar
          </div>
          <p className="font-bold">{priceGaps[0]?.commodity || "-"}</p>
          <p className="text-sm text-orange-600">{priceGaps[0]?.gapPct || 0}% antar wilayah</p>
        </div>
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <TrendingDown className="h-4 w-4 text-green-500" />
            Paling Stabil
          </div>
          <p className="font-bold">{volatility[volatility.length - 1]?.commodity || "-"}</p>
          <p className="text-sm text-green-600">CV {volatility[volatility.length - 1]?.cv || 0}%</p>
        </div>
      </div>
    </div>
  );
}
