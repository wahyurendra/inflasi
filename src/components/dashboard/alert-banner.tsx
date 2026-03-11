"use client";

import Link from "next/link";
import { AlertTriangle } from "lucide-react";

interface AlertItem {
  id: number;
  severity: "info" | "warning" | "critical";
  judul: string;
}

interface AlertBannerProps {
  alerts: AlertItem[];
}

const severityConfig = {
  critical: { bg: "bg-red-50", text: "text-red-700", dot: "bg-red-500" },
  warning: { bg: "bg-orange-50", text: "text-orange-700", dot: "bg-orange-500" },
  info: { bg: "bg-blue-50", text: "text-blue-700", dot: "bg-blue-500" },
};

export function AlertBanner({ alerts }: AlertBannerProps) {
  if (!alerts.length) return null;

  return (
    <div className="bg-white rounded-xl border p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-orange-500" />
          <h3 className="text-sm font-semibold text-gray-900">
            Alert Aktif ({alerts.length})
          </h3>
        </div>
        <Link
          href="/alerts"
          className="text-xs text-blue-600 hover:text-blue-700 font-medium"
        >
          Lihat Semua
        </Link>
      </div>
      <div className="space-y-2">
        {alerts.slice(0, 5).map((alert) => {
          const config = severityConfig[alert.severity];
          return (
            <div
              key={alert.id}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg ${config.bg}`}
            >
              <span className={`h-2 w-2 rounded-full ${config.dot}`} />
              <span className={`text-sm ${config.text}`}>{alert.judul}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
