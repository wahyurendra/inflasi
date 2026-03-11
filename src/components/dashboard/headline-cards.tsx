"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string;
  change?: number;
  subtext?: string;
}

function StatCard({ label, value, change, subtext }: StatCardProps) {
  const isPositive = change !== undefined && change > 0;
  const isNegative = change !== undefined && change < 0;

  return (
    <div className="bg-white rounded-xl border p-5">
      <p className="text-sm text-gray-500 font-medium">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      <div className="flex items-center gap-1.5 mt-2">
        {change !== undefined && (
          <>
            {isPositive ? (
              <TrendingUp className="h-4 w-4 text-red-500" />
            ) : isNegative ? (
              <TrendingDown className="h-4 w-4 text-green-500" />
            ) : (
              <Minus className="h-4 w-4 text-gray-400" />
            )}
            <span
              className={`text-sm font-medium ${
                isPositive
                  ? "text-red-600"
                  : isNegative
                    ? "text-green-600"
                    : "text-gray-500"
              }`}
            >
              {change > 0 ? "+" : ""}
              {change.toFixed(2)}%
            </span>
          </>
        )}
        {subtext && <span className="text-xs text-gray-400 ml-1">{subtext}</span>}
      </div>
    </div>
  );
}

interface HeadlineCardsProps {
  mtm: number | null;
  ytd: number | null;
  yoy: number | null;
  ihk: number | null;
  periode: string;
}

export function HeadlineCards({ mtm, ytd, yoy, ihk, periode }: HeadlineCardsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        label="Inflasi MtM"
        value={mtm !== null ? `${mtm > 0 ? "+" : ""}${mtm.toFixed(2)}%` : "-"}
        change={mtm ?? undefined}
        subtext={periode}
      />
      <StatCard
        label="Inflasi YtD"
        value={ytd !== null ? `${ytd > 0 ? "+" : ""}${ytd.toFixed(2)}%` : "-"}
        change={ytd ?? undefined}
        subtext={periode}
      />
      <StatCard
        label="Inflasi YoY"
        value={yoy !== null ? `${yoy > 0 ? "+" : ""}${yoy.toFixed(2)}%` : "-"}
        change={yoy ?? undefined}
        subtext={periode}
      />
      <StatCard
        label="IHK Pangan"
        value={ihk !== null ? ihk.toFixed(2) : "-"}
        subtext={periode}
      />
    </div>
  );
}
