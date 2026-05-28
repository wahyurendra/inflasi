"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface CommodityItem {
  namaDisplay: string;
  hargaTerakhir: number;
  perubahanMingguan: number;
  kategori: string;
}

interface CommodityRankingProps {
  data: CommodityItem[];
  title?: string;
}

export function CommodityRanking({
  data,
  title = "Komoditas Paling Naik",
}: CommodityRankingProps) {
  return (
    <div className="bg-card rounded-xl border p-5">
      <h3 className="text-sm font-semibold text-foreground mb-4">{title}</h3>
      <div className="space-y-3">
        {data.map((item, idx) => {
          const isUp = item.perubahanMingguan > 0;
          const isDown = item.perubahanMingguan < 0;

          return (
            <div key={item.namaDisplay} className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-muted-foreground w-5">
                  {idx + 1}.
                </span>
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {item.namaDisplay}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Rp {item.hargaTerakhir.toLocaleString("id-ID")}/kg
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                {isUp ? (
                  <TrendingUp className="h-3.5 w-3.5 text-red-500" />
                ) : isDown ? (
                  <TrendingDown className="h-3.5 w-3.5 text-green-500" />
                ) : (
                  <Minus className="h-3.5 w-3.5 text-muted-foreground" />
                )}
                <span
                  className={`text-sm font-semibold ${
                    isUp ? "text-red-500" : isDown ? "text-green-500" : "text-muted-foreground"
                  }`}
                >
                  {item.perubahanMingguan > 0 ? "+" : ""}
                  {item.perubahanMingguan.toFixed(1)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
