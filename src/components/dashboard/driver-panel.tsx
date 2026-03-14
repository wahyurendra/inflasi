"use client";

import { Cloud, Package, DollarSign, Calendar, Globe, Truck, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface Driver {
  name: string;
  contribution_pct: number;
  magnitude: number;
  direction: "naik" | "turun" | "neutral";
  detail: string;
}

interface DriverPanelProps {
  drivers: Driver[];
  commodity?: string;
}

const DRIVER_CONFIG: Record<string, { label: string; icon: typeof Cloud; color: string }> = {
  cuaca: { label: "Cuaca", icon: Cloud, color: "#3b82f6" },
  stok: { label: "Stok", icon: Package, color: "#f97316" },
  kurs: { label: "Kurs", icon: DollarSign, color: "#8b5cf6" },
  musiman: { label: "Musiman", icon: Calendar, color: "#22c55e" },
  global: { label: "Global", icon: Globe, color: "#ef4444" },
  logistik: { label: "Logistik", icon: Truck, color: "#6b7280" },
};

const DirectionIcon = ({ direction }: { direction: string }) => {
  if (direction === "naik") return <TrendingUp className="h-3.5 w-3.5 text-red-500" />;
  if (direction === "turun") return <TrendingDown className="h-3.5 w-3.5 text-green-500" />;
  return <Minus className="h-3.5 w-3.5 text-gray-400" />;
};

export function DriverPanel({ drivers, commodity }: DriverPanelProps) {
  if (!drivers?.length) {
    return (
      <div className="bg-white rounded-xl border p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">
          Driver Inflasi {commodity ? `— ${commodity}` : ""}
        </h3>
        <p className="text-sm text-gray-400">Data driver belum tersedia</p>
      </div>
    );
  }

  const maxPct = Math.max(...drivers.map((d) => d.contribution_pct));

  return (
    <div className="bg-white rounded-xl border p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">
        Driver Inflasi {commodity ? `— ${commodity}` : ""}
      </h3>

      {/* Stacked bar */}
      <div className="flex rounded-full h-4 overflow-hidden mb-4">
        {drivers
          .filter((d) => d.contribution_pct > 0)
          .map((d) => {
            const config = DRIVER_CONFIG[d.name] || { color: "#9ca3af" };
            return (
              <div
                key={d.name}
                className="h-full transition-all duration-300"
                style={{
                  width: `${d.contribution_pct}%`,
                  backgroundColor: config.color,
                  minWidth: d.contribution_pct > 3 ? "auto" : 0,
                }}
                title={`${config.label || d.name}: ${d.contribution_pct}%`}
              />
            );
          })}
      </div>

      {/* Driver list */}
      <div className="space-y-3">
        {drivers.map((d) => {
          const config = DRIVER_CONFIG[d.name] || {
            label: d.name,
            icon: Globe,
            color: "#9ca3af",
          };
          const Icon = config.icon;

          return (
            <div key={d.name} className="flex items-center gap-3">
              <div
                className="flex items-center justify-center w-8 h-8 rounded-lg"
                style={{ backgroundColor: `${config.color}15` }}
              >
                <Icon className="h-4 w-4" style={{ color: config.color }} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900">
                    {config.label}
                  </span>
                  <DirectionIcon direction={d.direction} />
                  <span className="text-xs font-semibold" style={{ color: config.color }}>
                    {d.contribution_pct.toFixed(1)}%
                  </span>
                </div>
                <p className="text-xs text-gray-500 truncate">{d.detail}</p>
              </div>
              <div className="w-20">
                <div className="h-1.5 bg-gray-100 rounded-full">
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${(d.contribution_pct / maxPct) * 100}%`,
                      backgroundColor: config.color,
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
