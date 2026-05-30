import type { Metadata } from "next";
import Link from "next/link";
import {
  Landmark,
  Banknote,
  Umbrella,
  GraduationCap,
  Grid3x3,
  ArrowRight,
} from "lucide-react";
import { Navbar, Footer } from "@/components/landing/premium-landing";

const siteUrl = process.env.NEXT_PUBLIC_APP_URL || "https://inflasi.id";

const description =
  "Solusi intelijen harga pangan inflasi.id untuk pemerintah & TPID, fintech, asuransi, dan riset — early warning, pemodelan risiko, asuransi parametrik, dan dataset penelitian.";

export const metadata: Metadata = {
  title: "Solusi per Sektor — Government, Fintech, Insurance, Research",
  description,
  alternates: { canonical: "/solutions" },
  openGraph: {
    type: "website",
    url: `${siteUrl}/solutions`,
    title: "Solusi per Sektor — Inflasi.id",
    description,
  },
  twitter: { card: "summary_large_image", title: "Solusi per Sektor — Inflasi.id", description },
};

const SOLUTIONS = [
  {
    id: "government",
    Icon: Landmark,
    sector: "Pemerintah & TPID",
    headline: "Deteksi dini tekanan inflasi untuk keputusan yang lebih cepat.",
    copy: "Pantau tekanan harga per wilayah, dapatkan early warning sebelum lonjakan, dan koordinasikan operasi pasar dengan data harian yang dapat diaudit.",
    points: [
      "Heatmap & ranking tekanan harga 38 provinsi",
      "Alert dini berbasis aturan & deteksi anomali",
      "Dukungan pengambilan keputusan TPID",
      "Analisis faktor pendorong per komoditas",
    ],
  },
  {
    id: "fintech",
    Icon: Banknote,
    sector: "Fintech & Lending",
    headline: "Sinyal harga pangan untuk pemodelan risiko kredit.",
    copy: "Gunakan tren harga dan indikator inflasi regional untuk credit scoring pertanian, embedded finance, dan penilaian risiko portofolio agrikultur.",
    points: [
      "API tren harga & inflasi regional",
      "Indikator risiko untuk kredit pertanian",
      "Data historis untuk backtesting model",
      "Integrasi langsung ke pipeline data Anda",
    ],
  },
  {
    id: "insurance",
    Icon: Umbrella,
    sector: "Asuransi",
    headline: "Dasar data untuk asuransi parametrik & indeks.",
    copy: "Manfaatkan sinyal harga dan cuaca tervalidasi sebagai basis produk asuransi indeks pertanian dan pemodelan risiko bencana harga.",
    points: [
      "Indeks harga & sinyal cuaca per wilayah",
      "Basis pemicu (trigger) asuransi parametrik",
      "Data tervalidasi & dapat diaudit",
      "Cakupan nasional hingga tingkat provinsi",
    ],
  },
  {
    id: "research",
    Icon: GraduationCap,
    sector: "Riset & Akademik",
    headline: "Dataset terbuka untuk riset ketahanan pangan.",
    copy: "Akses data historis harga, volatilitas, dan inflasi untuk riset ekonomi, kebijakan publik, dan ketahanan pangan — dengan metodologi yang transparan.",
    points: [
      "Dataset historis harga & inflasi",
      "Metodologi terbuka & terdokumentasi",
      "Kolaborasi riset & publikasi bersama",
      "Referensi sumber resmi pada tiap data",
    ],
  },
];

export default function SolutionsPage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    name: "Solusi per Sektor — Inflasi.id",
    description,
    url: `${siteUrl}/solutions`,
    inLanguage: "id-ID",
    publisher: { "@type": "Organization", name: "Inflasi.id", url: siteUrl },
  };

  return (
    <main className="landing-theme min-h-screen bg-background text-foreground">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <Navbar />

      {/* Hero */}
      <section className="relative overflow-hidden px-6 pb-12 pt-32 md:px-12 md:pt-40">
        <div aria-hidden className="pointer-events-none absolute inset-x-0 top-0 h-[480px] bg-[radial-gradient(circle_at_50%_0%,hsl(var(--primary)/0.26),transparent_60%)]" />
        <div aria-hidden className="pointer-events-none absolute inset-0 opacity-40 landing-grain" />
        <div className="relative mx-auto max-w-3xl text-center">
          <p className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-secondary">
            <Grid3x3 className="h-3.5 w-3.5" />
            Solusi per Sektor
          </p>
          <h1 className="text-balance text-4xl font-medium leading-[1.05] tracking-[-1.5px] md:text-6xl">
            Satu sinyal, <span className="font-serif-accent text-secondary">banyak manfaat</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-hero-subtitle opacity-90 md:text-lg">
            Intelijen harga pangan yang sama memberi nilai berbeda bagi tiap sektor. Pilih yang
            paling relevan untuk organisasi Anda.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
            {SOLUTIONS.map((s) => (
              <a
                key={s.id}
                href={`#${s.id}`}
                className="rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium text-muted-foreground transition hover:text-foreground"
              >
                {s.sector}
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* Sector sections */}
      {SOLUTIONS.map(({ id, Icon, sector, headline, copy, points }, idx) => (
        <section key={id} id={id} className="scroll-mt-24 px-6 py-12 md:px-12 md:py-16">
          <div className="mx-auto max-w-6xl">
            <div
              className={`grid items-center gap-8 lg:grid-cols-2 ${
                idx % 2 === 1 ? "lg:[&>*:first-child]:order-2" : ""
              }`}
            >
              <div>
                <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary/15 text-secondary">
                  <Icon className="h-6 w-6" />
                </span>
                <p className="mt-5 text-xs font-semibold uppercase tracking-[0.2em] text-secondary">
                  {sector}
                </p>
                <h2 className="mt-3 text-balance text-2xl font-medium leading-snug tracking-[-0.5px] text-foreground md:text-3xl">
                  {headline}
                </h2>
                <p className="mt-4 max-w-xl text-base leading-7 text-muted-foreground">{copy}</p>
                <Link
                  href="/partner"
                  className="mt-6 inline-flex items-center gap-1.5 text-sm font-semibold text-secondary hover:underline"
                >
                  Ajukan kemitraan <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
              <div className="liquid-glass rounded-3xl p-7">
                <ul className="space-y-3">
                  {points.map((p) => (
                    <li key={p} className="flex items-start gap-3 text-sm leading-6 text-muted-foreground">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-secondary" />
                      {p}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>
      ))}

      {/* CTA */}
      <section className="px-6 py-20 md:px-12 md:py-24">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-balance text-3xl font-medium leading-tight tracking-[-1px] md:text-5xl">
            Tidak menemukan sektor Anda?
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-base leading-7 text-muted-foreground">
            Ceritakan kebutuhan Anda — kami akan menyusun model kolaborasi yang tepat.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link href="/partner" className="inline-flex h-12 items-center justify-center rounded-full bg-secondary px-8 text-base font-semibold text-secondary-foreground transition hover:bg-secondary/90">
              Jadi Mitra <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
            <Link href="/contact" className="inline-flex h-12 items-center justify-center rounded-full border border-white/15 bg-white/5 px-8 text-base font-medium text-foreground transition hover:bg-white/10">
              Hubungi Kami
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
