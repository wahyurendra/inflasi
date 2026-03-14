"use client";

import { useAlerts } from "@/hooks/use-alerts";

const severityConfig = {
  critical: {
    bg: "border-l-red-500",
    badge: "bg-red-100 text-red-700",
    label: "Critical",
  },
  warning: {
    bg: "border-l-orange-500",
    badge: "bg-orange-100 text-orange-700",
    label: "Warning",
  },
  info: {
    bg: "border-l-blue-500",
    badge: "bg-blue-100 text-blue-700",
    label: "Info",
  },
};

export default function AlertsPage() {
  const { data: alertResponse, isLoading } = useAlerts(true, undefined, 20);
  const alerts = alertResponse?.data ?? [];

  const criticalCount = alerts.filter((a) => a.severity === "critical").length;
  const warningCount = alerts.filter((a) => a.severity === "warning").length;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-gray-900">Alert Center</h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Komoditas dan wilayah yang memerlukan perhatian
        </p>
      </div>

      {/* Summary */}
      <div className="flex gap-4">
        <div className="flex items-center gap-2 px-4 py-2 bg-red-50 rounded-lg">
          <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
          <span className="text-sm font-medium text-red-700">
            {criticalCount} Critical
          </span>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-orange-50 rounded-lg">
          <span className="h-2.5 w-2.5 rounded-full bg-orange-500" />
          <span className="text-sm font-medium text-orange-700">
            {warningCount} Warning
          </span>
        </div>
      </div>

      {/* Alert List */}
      <div className="space-y-4">
        {isLoading && (
          <p className="text-sm text-gray-500">Memuat alert...</p>
        )}
        {!isLoading && alerts.length === 0 && (
          <div className="bg-white rounded-xl border p-8 text-center">
            <p className="text-sm text-gray-500">Tidak ada alert aktif saat ini.</p>
          </div>
        )}
        {alerts.map((alert) => {
          const config = severityConfig[alert.severity as keyof typeof severityConfig] ?? severityConfig.info;
          return (
            <div
              key={alert.id}
              className={`bg-white rounded-xl border border-l-4 ${config.bg} p-5`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded-full ${config.badge}`}
                    >
                      {config.label}
                    </span>
                    <span className="text-xs text-gray-400">{alert.tanggal}</span>
                  </div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-1">
                    {alert.judul}
                  </h4>
                  <p className="text-sm text-gray-600">{alert.deskripsi}</p>
                  <div className="flex gap-4 mt-3">
                    <span className="text-xs text-gray-500">
                      Komoditas: <strong>{alert.commodity.nama}</strong>
                    </span>
                    <span className="text-xs text-gray-500">
                      Wilayah: <strong>{alert.region.nama}</strong>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
