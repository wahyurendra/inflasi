"use client";

interface InsightCardProps {
  judul: string;
  konten: string;
  tanggal: string;
}

export function InsightCard({ judul, konten, tanggal }: InsightCardProps) {
  // Show first 3 lines of content
  const preview = konten.split("\n").filter(Boolean).slice(0, 4).join("\n");

  return (
    <div className="bg-white rounded-xl border p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-900">Insight Hari Ini</h3>
        <span className="text-xs text-gray-400">{tanggal}</span>
      </div>
      <p className="text-sm text-gray-600 whitespace-pre-line leading-relaxed">
        {preview}
      </p>
    </div>
  );
}
