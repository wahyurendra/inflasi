"use client";

interface RegionItem {
  namaProvinsi: string;
  avgPriceChange: number;
  alertCount: number;
}

interface RegionRankingProps {
  data: RegionItem[];
  title?: string;
}

export function RegionRanking({
  data,
  title = "Wilayah Paling Tertekan",
}: RegionRankingProps) {
  return (
    <div className="bg-white rounded-xl border p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="space-y-3">
        {data.map((item, idx) => (
          <div key={item.namaProvinsi} className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-gray-400 w-5">
                {idx + 1}.
              </span>
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {item.namaProvinsi}
                </p>
                {item.alertCount > 0 && (
                  <p className="text-xs text-orange-500">
                    {item.alertCount} alert aktif
                  </p>
                )}
              </div>
            </div>
            <span
              className={`text-sm font-semibold ${
                item.avgPriceChange > 5
                  ? "text-red-600"
                  : item.avgPriceChange > 2
                    ? "text-orange-500"
                    : "text-gray-600"
              }`}
            >
              +{item.avgPriceChange.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
