"use client";

interface InsightCardProps {
  judul: string;
  konten: string;
  tanggal: string;
}

export function InsightCard({ judul, konten, tanggal }: InsightCardProps) {
  const preview = konten.split("\n").filter(Boolean).slice(0, 4).join("\n");

  return (
    <div className="bg-card rounded-xl border p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-foreground">Insight Hari Ini</h3>
        <span className="text-xs text-muted-foreground">{tanggal}</span>
      </div>
      <p className="text-sm text-muted-foreground whitespace-pre-line leading-relaxed">
        {preview}
      </p>
    </div>
  );
}
