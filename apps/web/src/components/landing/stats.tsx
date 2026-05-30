const STATS = [
  { value: "{STAT_1_VALUE}", label: "{STAT_1_LABEL}" },
  { value: "{STAT_2_VALUE}", label: "{STAT_2_LABEL}" },
  { value: "{STAT_3_VALUE}", label: "{STAT_3_LABEL}" },
  { value: "{STAT_4_VALUE}", label: "{STAT_4_LABEL}" },
];

export function LandingStats() {
  return (
    <section className="border-y bg-muted/40 py-10 px-4">
      <div className="max-w-4xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-6">
        {STATS.map((s) => (
          <div key={s.label} className="text-center">
            <p className="text-3xl sm:text-4xl font-bold text-primary tracking-tight">
              {s.value}
            </p>
            <p className="text-sm text-muted-foreground mt-1">{s.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
