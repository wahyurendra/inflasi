import type { Metadata } from "next";
import {
  Landmark,
  Building2,
  GraduationCap,
  Newspaper,
  Code2,
  Sprout,
  Database,
  LayoutDashboard,
  FlaskConical,
  Handshake,
  ShieldCheck,
  MapPin,
  TrendingUp,
  Clock,
} from "lucide-react";
import { Navbar, Footer } from "@/components/landing/premium-landing";
import { PartnerForm } from "@/components/landing/partner-form";

const siteUrl = process.env.NEXT_PUBLIC_APP_URL || "https://inflasi.id";

const description =
  "Berkolaborasi dengan inflasi.id: akses data harga pangan tervalidasi 38 provinsi, dashboard khusus, riset bersama, dan integrasi API untuk pemerintah, institusi keuangan, akademisi, dan pengembang.";

export const metadata: Metadata = {
  title: "Partner with Us — Kemitraan Intelijen Pangan",
  description,
  alternates: { canonical: "/partner" },
  openGraph: {
    type: "website",
    url: `${siteUrl}/partner`,
    title: "Partner with Us — Inflasi.id",
    description,
  },
  twitter: {
    card: "summary_large_image",
    title: "Partner with Us — Inflasi.id",
    description,
  },
};

const PARTNER_TYPES = [
  {
    Icon: Landmark,
    title: "Pemerintah & TPID",
    copy: "Deteksi dini tekanan inflasi regional, dukung pengambilan keputusan TPID, dan koordinasikan operasi pasar dengan data harga harian per wilayah.",
  },
  {
    Icon: Building2,
    title: "Institusi Keuangan",
    copy: "Manfaatkan sinyal harga pangan teragregasi untuk asuransi parametrik, pemodelan risiko, dan analisis kredit pertanian.",
  },
  {
    Icon: GraduationCap,
    title: "Riset & Akademik",
    copy: "Akses dataset historis harga, volatilitas, dan inflasi untuk riset ketahanan pangan, ekonomi, dan kebijakan publik.",
  },
  {
    Icon: Newspaper,
    title: "Media & NGO",
    copy: "Gunakan data dan visualisasi tervalidasi untuk jurnalisme data, advokasi, dan pemantauan ketahanan pangan masyarakat.",
  },
  {
    Icon: Code2,
    title: "Pengembang & Startup",
    copy: "Bangun produk di atas API harga pangan: sinyal harga, tren komoditas, dan indikator inflasi regional yang siap pakai.",
  },
  {
    Icon: Sprout,
    title: "Petani & Rantai Pasok",
    copy: "Pahami pergerakan harga, peluang pasokan antarwilayah, dan disparitas harga untuk keputusan distribusi yang lebih baik.",
  },
];

const MODELS = [
  {
    Icon: Database,
    title: "Akses Data & API",
    copy: "Endpoint REST untuk harga harian, ranking wilayah, forecast, dan deteksi anomali — dengan dokumentasi dan SLA.",
  },
  {
    Icon: LayoutDashboard,
    title: "Dashboard Khusus",
    copy: "Tampilan terkustomisasi untuk wilayah, komoditas, atau indikator spesifik sesuai kebutuhan institusi Anda.",
  },
  {
    Icon: FlaskConical,
    title: "Riset Bersama",
    copy: "Kolaborasi metodologi, validasi model, dan publikasi bersama dengan tim data inflasi.id.",
  },
  {
    Icon: Handshake,
    title: "Integrasi & White-label",
    copy: "Sematkan intelijen harga pangan ke dalam platform Anda, atau jalankan instans white-label untuk program internal.",
  },
];

const STATS = [
  { Icon: MapPin, value: "38", label: "Provinsi terpantau" },
  { Icon: TrendingUp, value: "10+", label: "Komoditas strategis" },
  { Icon: Clock, value: "24/7", label: "Data feed real-time" },
  { Icon: ShieldCheck, value: "AI", label: "Validasi & forecast" },
];

export default function PartnerPage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    name: "Partner with Us — Inflasi.id",
    description,
    url: `${siteUrl}/partner`,
    inLanguage: "id-ID",
    publisher: { "@type": "Organization", name: "Inflasi.id", url: siteUrl },
  };

  return (
    <main className="landing-theme min-h-screen bg-background text-foreground">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <Navbar />

      {/* Hero */}
      <section className="relative overflow-hidden px-6 pb-16 pt-32 md:px-12 md:pt-40">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-[520px] bg-[radial-gradient(circle_at_50%_0%,hsl(var(--primary)/0.28),transparent_60%)]"
        />
        <div aria-hidden className="pointer-events-none absolute inset-0 opacity-40 landing-grain" />
        <div className="relative mx-auto max-w-4xl text-center">
          <p className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-secondary">
            <Handshake className="h-3.5 w-3.5" />
            Partner with us
          </p>
          <h1 className="text-balance text-4xl font-medium leading-[1.05] tracking-[-1.5px] md:text-6xl lg:text-7xl">
            Bangun di atas intelijen{" "}
            <span className="font-serif-accent text-secondary">harga pangan</span> Indonesia.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-hero-subtitle opacity-90 md:text-lg">
            inflasi.id membuka data, dashboard, dan kapabilitas AI-nya untuk pemerintah,
            institusi keuangan, peneliti, media, dan pengembang yang ingin memperkuat ketahanan
            pangan nasional.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <a
              href="#kontak"
              className="inline-flex h-12 items-center justify-center rounded-full bg-secondary px-8 text-base font-semibold text-secondary-foreground transition hover:bg-secondary/90"
            >
              Ajukan Kemitraan
            </a>
            <a
              href="#model"
              className="inline-flex h-12 items-center justify-center rounded-full border border-white/15 bg-white/5 px-8 text-base font-medium text-foreground backdrop-blur transition hover:bg-white/10"
            >
              Lihat Model Kemitraan
            </a>
          </div>
        </div>

        {/* Stats */}
        <div className="relative mx-auto mt-16 grid max-w-4xl grid-cols-2 gap-3 md:grid-cols-4">
          {STATS.map(({ Icon, value, label }) => (
            <div key={label} className="liquid-glass rounded-2xl px-5 py-5 text-center">
              <Icon className="mx-auto h-5 w-5 text-secondary" />
              <p className="mt-3 text-2xl font-bold text-foreground">{value}</p>
              <p className="mt-1 text-xs text-muted-foreground">{label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Partner types */}
      <section className="px-6 py-20 md:px-12 md:py-28">
        <div className="mx-auto max-w-6xl">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-balance text-3xl font-medium leading-tight tracking-[-1px] md:text-5xl">
              Siapa yang kami ajak <span className="font-serif-accent text-secondary">berkolaborasi</span>
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
              Intelijen harga pangan jadi lebih bernilai ketika dibagikan ke seluruh ekosistem.
            </p>
          </div>
          <div className="mt-14 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {PARTNER_TYPES.map(({ Icon, title, copy }) => (
              <div
                key={title}
                className="liquid-glass rounded-3xl p-7 transition hover:border-secondary/30"
              >
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-secondary/15 text-secondary">
                  <Icon className="h-5 w-5" />
                </span>
                <h3 className="mt-5 text-lg font-semibold text-foreground">{title}</h3>
                <p className="mt-2.5 text-sm leading-6 text-muted-foreground">{copy}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Partnership models */}
      <section id="model" className="px-6 py-20 md:px-12 md:py-28">
        <div className="mx-auto max-w-6xl">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-balance text-3xl font-medium leading-tight tracking-[-1px] md:text-5xl">
              Model <span className="font-serif-accent text-secondary">kemitraan</span>
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
              Pilih bentuk kolaborasi yang paling sesuai — dari akses data hingga integrasi penuh.
            </p>
          </div>
          <div className="mt-14 grid gap-4 md:grid-cols-2">
            {MODELS.map(({ Icon, title, copy }) => (
              <div key={title} className="liquid-glass flex gap-5 rounded-3xl p-7">
                <span className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary/15 text-primary">
                  <Icon className="h-6 w-6" />
                </span>
                <div>
                  <h3 className="text-lg font-semibold text-foreground">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact form */}
      <section id="kontak" className="px-6 py-20 md:px-12 md:py-28">
        <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div className="lg:sticky lg:top-28">
            <h2 className="text-balance text-3xl font-medium leading-tight tracking-[-1px] md:text-5xl">
              Mari <span className="font-serif-accent text-secondary">mulai percakapan</span>
            </h2>
            <p className="mt-5 max-w-md text-base leading-7 text-muted-foreground">
              Ceritakan kebutuhan organisasi Anda. Tim kami akan menyusun model kolaborasi yang
              tepat dan merespons dalam 2–3 hari kerja.
            </p>
            <ul className="mt-8 space-y-3 text-sm text-muted-foreground">
              {[
                "Data harga pangan tervalidasi 38 provinsi",
                "Dukungan teknis & dokumentasi API",
                "Kepatuhan tata kelola data",
              ].map((item) => (
                <li key={item} className="flex items-center gap-3">
                  <ShieldCheck className="h-4 w-4 shrink-0 text-secondary" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <PartnerForm />
        </div>
      </section>

      <Footer />
    </main>
  );
}
