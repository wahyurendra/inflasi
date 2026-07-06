import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, Bell, LineChart, Map } from "lucide-react";
import { Providers } from "@/components/providers";

const highlights = [
  {
    Icon: Map,
    title: "Heatmap 38 provinsi",
    copy: "Tekanan harga pangan nasional terbaca dalam hitungan detik.",
  },
  {
    Icon: LineChart,
    title: "Prediksi AI 1–3 bulan",
    copy: "Kenali risiko lonjakan sebelum menjadi krisis.",
  },
  {
    Icon: Bell,
    title: "Peringatan dini real-time",
    copy: "Anomali harga terdeteksi dan terkirim otomatis.",
  },
];

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Providers>
      <div className="min-h-screen lg:grid lg:grid-cols-[1.05fr_1fr]">
        {/* Panel brand — nuansa landing, hanya desktop. Gradien statis saja. */}
        <aside className="landing-theme relative hidden flex-col justify-between overflow-hidden p-10 lg:flex xl:p-14">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0"
            style={{
              background: [
                "radial-gradient(circle at 20% 0%, hsl(var(--primary) / 0.30), transparent 55%)",
                "radial-gradient(ellipse 50% 40% at 85% 80%, hsl(var(--secondary) / 0.10), transparent 70%)",
              ].join(", "),
            }}
          />
          <div aria-hidden className="absolute inset-0 landing-grid opacity-50 [animation:none]" />

          <Link href="/welcome" className="relative z-10 flex w-fit items-center gap-3">
            <Image src="/logo.svg" alt="INFLASI ID" width={40} height={40} className="h-10 w-10 rounded-full" />
            <span className="text-xl font-bold tracking-tight text-foreground">inflasi.id</span>
          </Link>

          <div className="relative z-10 max-w-md">
            <h1 className="text-balance text-3xl font-medium leading-tight tracking-[-1px] text-foreground xl:text-4xl">
              Intelijen inflasi pangan, <span className="font-serif-accent text-secondary">dalam satu dashboard.</span>
            </h1>
            <ul className="mt-8 space-y-5">
              {highlights.map(({ Icon, title, copy }) => (
                <li key={title} className="flex items-start gap-4">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-secondary/25 bg-secondary/10 text-secondary">
                    <Icon className="h-5 w-5" />
                  </span>
                  <div>
                    <p className="font-semibold text-foreground">{title}</p>
                    <p className="mt-0.5 text-sm leading-6 text-muted-foreground">{copy}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <p className="relative z-10 text-xs text-muted-foreground">
            © 2026 inflasi.id — Platform Intelijen Inflasi Pangan Indonesia
          </p>
        </aside>

        {/* Sisi form */}
        <main className="relative flex min-h-screen flex-col items-center justify-center bg-background p-4 sm:p-8">
          <Link
            href="/welcome"
            className="absolute left-4 top-4 inline-flex items-center gap-1.5 rounded-full px-3 py-2 text-sm text-muted-foreground transition hover:text-foreground sm:left-6 sm:top-6"
          >
            <ArrowLeft className="h-4 w-4" />
            Beranda
          </Link>

          <div className="w-full max-w-md">
            {/* Header ringkas untuk mobile (panel brand tersembunyi) */}
            <div className="mb-8 flex flex-col items-center text-center lg:hidden">
              <Image src="/logo.svg" alt="INFLASI ID" width={48} height={48} className="h-12 w-12 rounded-full" />
              <p className="mt-3 text-xl font-bold tracking-tight">inflasi.id</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Intelijen Inflasi Pangan Indonesia
              </p>
            </div>
            {children}
          </div>
        </main>
      </div>
    </Providers>
  );
}
