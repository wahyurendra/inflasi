import type { Metadata } from "next";
import Link from "next/link";
import {
  Workflow,
  Database,
  ShieldCheck,
  MapPin,
  Camera,
  ScanSearch,
  GitMerge,
  CalendarClock,
  Layers,
} from "lucide-react";
import { Navbar, Footer } from "@/components/landing/premium-landing";

const siteUrl = process.env.NEXT_PUBLIC_APP_URL || "https://inflasi.id";

const description =
  "Metodologi inflasi.id: sumber data resmi, cara perhitungan harga & inflasi, validasi data crowdsourced (GPS, peer-review, deteksi anomali), dan cakupan 38 provinsi.";

export const metadata: Metadata = {
  title: "Metodologi, Validasi & Cakupan Data",
  description,
  alternates: { canonical: "/methodology" },
  openGraph: {
    type: "website",
    url: `${siteUrl}/methodology`,
    title: "Metodologi — Inflasi.id",
    description,
  },
  twitter: { card: "summary_large_image", title: "Metodologi — Inflasi.id", description },
};

const SOURCES = [
  ["PIHPS — Bank Indonesia", "Harga pangan strategis harian per wilayah"],
  ["BPS", "Inflasi bulanan (MtM/YtD/YoY) & Indeks Harga Konsumen"],
  ["BMKG", "Data cuaca & peringatan iklim per wilayah"],
  ["Bank Indonesia (JISDOR)", "Kurs referensi USD/IDR"],
  ["FAO", "Food Price Index global"],
  ["Fed New York (GSCPI)", "Indeks tekanan rantai pasok global"],
  ["Bapanas", "Status neraca & stok pangan"],
  ["World Bank / EIA", "Harga komoditas & energi global"],
];

const PIPELINE = [
  { Icon: Database, title: "Ingest", copy: "ETL terjadwal menarik data dari sumber resmi setiap hari, dinormalisasi per wilayah & komoditas." },
  { Icon: GitMerge, title: "Agregasi", copy: "Data publik, crowdsourced, dan referensi resmi digabung menjadi satu basis yang konsisten." },
  { Icon: Layers, title: "Analitik", copy: "Risk score, deteksi anomali, analisis driver, dan forecast multi-horizon dihitung otomatis." },
  { Icon: CalendarClock, title: "Publikasi", copy: "Dashboard, alert, dan artikel harian diperbarui — siap dibaca dalam hitungan detik." },
];

const VALIDATION = [
  { Icon: MapPin, title: "Geofencing GPS", copy: "Laporan harga masyarakat diverifikasi lokasinya agar sesuai dengan pasar yang dilaporkan." },
  { Icon: Camera, title: "Bukti foto & struk", copy: "Foto harga/struk menyertai laporan untuk memungkinkan audit dan verifikasi silang." },
  { Icon: ScanSearch, title: "Deteksi anomali", copy: "Nilai yang menyimpang jauh dari distribusi wilayah ditandai dan tidak langsung dipakai." },
  { Icon: ShieldCheck, title: "Peer-review & trust score", copy: "Kontributor saling memvalidasi; reputasi kontributor memengaruhi bobot laporan." },
];

export default function MethodologyPage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    name: "Metodologi — Inflasi.id",
    description,
    url: `${siteUrl}/methodology`,
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
            <Workflow className="h-3.5 w-3.5" />
            Metodologi
          </p>
          <h1 className="text-balance text-4xl font-medium leading-[1.05] tracking-[-1.5px] md:text-6xl">
            Bagaimana data kami <span className="font-serif-accent text-secondary">dihasilkan</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-hero-subtitle opacity-90 md:text-lg">
            Transparansi adalah inti kepercayaan. Berikut sumber data, cara perhitungan, proses
            validasi, dan cakupan yang menjadi dasar setiap angka di inflasi.id.
          </p>
        </div>
      </section>

      {/* Methodology — sources & pipeline */}
      <section id="methodology" className="scroll-mt-24 px-6 py-16 md:px-12 md:py-20">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-balance text-3xl font-medium leading-tight tracking-[-1px] md:text-4xl">
            Sumber data &amp; <span className="font-serif-accent text-secondary">pipeline</span>
          </h2>
          <p className="mt-3 max-w-2xl text-base leading-7 text-muted-foreground">
            Kami menggabungkan beberapa sumber resmi menjadi satu basis data yang konsisten dan
            dapat diaudit — bukan opini, melainkan angka yang dapat ditelusuri.
          </p>

          <div className="mt-10 grid gap-3 sm:grid-cols-2">
            {SOURCES.map(([name, copy]) => (
              <div key={name} className="liquid-glass flex items-start gap-3 rounded-2xl p-5">
                <Database className="mt-0.5 h-4 w-4 shrink-0 text-secondary" />
                <div>
                  <p className="text-sm font-semibold text-foreground">{name}</p>
                  <p className="mt-1 text-xs leading-5 text-muted-foreground">{copy}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-4">
            {PIPELINE.map(({ Icon, title, copy }, i) => (
              <div key={title} className="liquid-glass rounded-3xl p-6">
                <div className="flex items-center justify-between">
                  <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-primary/15 text-primary">
                    <Icon className="h-5 w-5" />
                  </span>
                  <span className="text-sm font-semibold text-secondary">0{i + 1}</span>
                </div>
                <h3 className="mt-5 text-base font-semibold text-foreground">{title}</h3>
                <p className="mt-2 text-xs leading-5 text-muted-foreground">{copy}</p>
              </div>
            ))}
          </div>

          <div className="liquid-glass mt-6 rounded-3xl p-7">
            <h3 className="text-lg font-semibold text-foreground">Cara perhitungan</h3>
            <ul className="mt-4 space-y-2.5 text-sm leading-6 text-muted-foreground">
              <li>• <span className="text-foreground">Perubahan harga</span> dihitung sebagai persentase terhadap periode pembanding (harian, mingguan, bulanan).</li>
              <li>• <span className="text-foreground">Tekanan wilayah</span> adalah rata-rata perubahan mingguan seluruh komoditas terpantau di provinsi tersebut.</li>
              <li>• <span className="text-foreground">Volatilitas</span> diukur dengan koefisien variasi (CV) harga 30 hari terakhir.</li>
              <li>• <span className="text-foreground">Analisis driver</span> menggunakan weighted heuristic atas sinyal cuaca, stok, kurs, musiman, harga global, dan logistik.</li>
              <li>• <span className="text-foreground">Forecast</span> menghasilkan proyeksi multi-horizon dengan interval kuantil (p10/p50/p90).</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Validation */}
      <section id="validation" className="scroll-mt-24 px-6 py-16 md:px-12 md:py-20">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-balance text-3xl font-medium leading-tight tracking-[-1px] md:text-4xl">
            Validasi <span className="font-serif-accent text-secondary">data</span>
          </h2>
          <p className="mt-3 max-w-2xl text-base leading-7 text-muted-foreground">
            Laporan harga dari masyarakat memperkaya cakupan, tetapi hanya masuk setelah melewati
            beberapa lapis pemeriksaan otomatis dan komunitas.
          </p>
          <div className="mt-10 grid gap-4 md:grid-cols-2">
            {VALIDATION.map(({ Icon, title, copy }) => (
              <div key={title} className="liquid-glass flex gap-5 rounded-3xl p-7">
                <span className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-secondary/15 text-secondary">
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

      {/* Coverage */}
      <section id="coverage" className="scroll-mt-24 px-6 py-16 md:px-12 md:py-24">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-balance text-3xl font-medium leading-tight tracking-[-1px] md:text-4xl">
            Cakupan <span className="font-serif-accent text-secondary">data</span>
          </h2>
          <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["38", "Provinsi terpantau"],
              ["10+", "Komoditas strategis"],
              ["Harian", "Frekuensi pembaruan"],
              ["Multi-horizon", "Forecast (7/14/30 hari)"],
            ].map(([value, label]) => (
              <div key={label} className="liquid-glass rounded-2xl p-6 text-center">
                <p className="text-3xl font-bold text-foreground">{value}</p>
                <p className="mt-2 text-xs text-muted-foreground">{label}</p>
              </div>
            ))}
          </div>
          <p className="mt-6 max-w-2xl text-sm leading-6 text-muted-foreground">
            Cakupan mencakup tingkat nasional dan provinsi untuk komoditas pangan strategis
            (beras, cabai, bawang, telur, daging, minyak goreng, gula, dan lainnya). Angka bersifat
            indikatif dan dapat direvisi seiring pemutakhiran data sumber, serta tidak menggantikan
            rilis statistik resmi.
          </p>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 pb-24 md:px-12">
        <div className="mx-auto max-w-4xl rounded-3xl border border-white/10 bg-white/[0.025] p-8 text-center md:p-10">
          <p className="text-sm text-muted-foreground">
            Punya pertanyaan tentang metodologi atau ingin akses dataset?
          </p>
          <div className="mt-4 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link href="/contact" className="inline-flex h-11 items-center justify-center rounded-full bg-secondary px-7 text-sm font-semibold text-secondary-foreground transition hover:bg-secondary/90">
              Hubungi Kami
            </Link>
            <Link href="/blog" className="inline-flex h-11 items-center justify-center rounded-full border border-white/15 bg-white/5 px-7 text-sm font-medium text-foreground transition hover:bg-white/10">
              Baca Analisis Harian
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
