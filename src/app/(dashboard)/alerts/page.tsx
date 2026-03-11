import { AlertTriangle } from "lucide-react";

const mockAlerts = [
  {
    id: 1,
    tanggal: "10 Mar 2026",
    severity: "critical",
    judul: "Cabai rawit: Kenaikan harga 12% dalam 7 hari",
    deskripsi:
      "Harga cabai rawit naik 12% dalam 7 hari terakhir di 5 provinsi. Wilayah terdampak: Jawa Barat, Jawa Timur, Jawa Tengah, Sumatera Utara, Lampung. Harga saat ini: Rp 85.000/kg (median nasional).",
    komoditas: "Cabai Rawit",
    wilayah: "5 provinsi",
    nilaiAktual: 12.0,
  },
  {
    id: 2,
    tanggal: "9 Mar 2026",
    severity: "warning",
    judul: "Bawang merah: Volatilitas tinggi 2 minggu berturut",
    deskripsi:
      "Bawang merah menunjukkan CV 18.3% selama 14 hari terakhir (threshold: 15%). Terutama di wilayah Brebes dan Nganjuk.",
    komoditas: "Bawang Merah",
    wilayah: "Nasional",
    nilaiAktual: 18.3,
  },
  {
    id: 3,
    tanggal: "9 Mar 2026",
    severity: "critical",
    judul: "Papua: 3 komoditas naik >5% bersamaan",
    deskripsi:
      "Di Papua, 3 komoditas mengalami kenaikan >5% dalam 7 hari: beras (+5%), telur ayam (+7%), gula pasir (+4%).",
    komoditas: "Multi-komoditas",
    wilayah: "Papua",
    nilaiAktual: 3,
  },
  {
    id: 4,
    tanggal: "8 Mar 2026",
    severity: "warning",
    judul: "Maluku: Beras dan minyak goreng volatilitas tinggi",
    deskripsi:
      "Di Maluku, beras dan minyak goreng menunjukkan volatilitas tinggi selama 2 minggu terakhir.",
    komoditas: "Beras, Minyak Goreng",
    wilayah: "Maluku",
    nilaiAktual: 16.5,
  },
];

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
  const criticalCount = mockAlerts.filter((a) => a.severity === "critical").length;
  const warningCount = mockAlerts.filter((a) => a.severity === "warning").length;

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
        {mockAlerts.map((alert) => {
          const config = severityConfig[alert.severity as keyof typeof severityConfig];
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
                      Komoditas: <strong>{alert.komoditas}</strong>
                    </span>
                    <span className="text-xs text-gray-500">
                      Wilayah: <strong>{alert.wilayah}</strong>
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
