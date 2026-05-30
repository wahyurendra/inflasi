import type { Metadata } from "next";
import Link from "next/link";
import {
  Radar,
  Lightbulb,
  Map,
  MessageSquare,
  ShieldCheck,
  Database,
  Sparkles,
  Users,
  ArrowRight,
} from "lucide-react";
import { Navbar, Footer } from "@/components/landing/premium-landing";

const siteUrl = process.env.NEXT_PUBLIC_APP_URL || "https://inflasi.id";

const description =
  "inflasi.id adalah sistem pemantauan inflasi pangan berbasis AI untuk Indonesia — membaca sinyal dini tekanan harga, menjelaskan penyebabnya, dan memprioritaskan wilayah serta komoditas yang perlu perhatian.";

export const metadata: Metadata = {
  title: "Tentang Kami — Intelijen Inflasi Pangan",
  description,
  alternates: { canonical: "/about" },
  openGraph: {
    type: "website",
    url: `${siteUrl}/about`,
    title: "Tentang Inflasi.id",
    description,
  },
  twitter: {
    card: "summary_large_image",
    title: "Tentang Inflasi.id",
    description,
  },
};

const WHAT = [
  {
    Icon: Radar,
    title: "Sinyal dini",
    copy: "Mendeteksi tekanan harga pangan sebelum menjadi krisis, dengan alert berbasis aturan dan deteksi anomali.",
  },
  {
    Icon: Lightbulb,
    title: "Menjelaskan penyebab",
    copy: "Bukan hanya menampilkan angka, tetapi mengurai faktor pendorong: cuaca, stok, kurs, musiman, harga global, dan logistik.",
  },
  {
    Icon: Map,
    title: "Prioritas wilayah",
    copy: "Heatmap dan ranking 38 provinsi membantu memprioritaskan intervensi pada wilayah dan komoditas yang paling tertekan.",
  },
  {
    Icon: MessageSquare,
    title: "Tanya langsung ke data",
    copy: "AI assistant menjawab pertanyaan kontekstual berbasis data — bukan opini — dalam hitungan detik.",
  },
];

const DIFF = [
  {
    Icon: Sparkles,
    title: "Menjelaskan, bukan sekadar menampilkan",
    copy: "Dashboard inflasi biasa berhenti pada grafik. inflasi.id menjelaskan mengapa angka berubah.",
  },
  {
    Icon: ShieldCheck,
    title: "Data tervalidasi & crowdsourced",
    copy: "Menggabungkan sumber resmi dengan laporan harga masyarakat yang divalidasi GPS, peer-review, dan deteksi anomali.",
  },
  {
    Icon: Database,
    title: "Satu sumber kebenaran",
    copy: "Menyatukan beberapa sumber data resmi menjadi satu platform yang konsisten dan dapat diaudit.",
  },
];

const VALUES = [
  { title: "Berbasis data", copy: "Setiap insight bersumber dari data, dapat ditelusuri, dan bebas dari spekulasi." },
  { title: "Transparan", copy: "Metodologi terbuka dan setiap artikel menyertakan referensi sumber resmi." },
  { title: "Untuk publik", copy: "Dashboard publik tetap gratis; data dibagikan untuk memperkuat ketahanan pangan." },
];

export default function AboutPage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "AboutPage",
    name: "Tentang Inflasi.id",
    description,
    url: `${siteUrl}/about`,
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
            <Users className="h-3.5 w-3.5" />
            Tentang Kami
          </p>
          <h1 className="text-balance text-4xl font-medium leading-[1.05] tracking-[-1.5px] md:text-6xl lg:text-7xl">
            Membaca sinyal dini{" "}
            <span className="font-serif-accent text-secondary">inflasi pangan</span> Indonesia.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-hero-subtitle opacity-90 md:text-lg">
            inflasi.id adalah sistem pemantauan inflasi pangan berbasis AI yang membantu pengambil
            kebijakan, analis, dan masyarakat membaca sinyal dini tekanan harga, memahami
            penyebabnya, dan memprioritaskan intervensi.
          </p>
        </div>
      </section>

      {/* Mission */}
      <section className="px-6 py-16 md:px-12 md:py-20">
        <div className="mx-auto max-w-4xl">
          <div className="liquid-glass gold-glow rounded-3xl p-8 text-center md:p-12">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-secondary">Misi Kami</p>
            <p className="mt-5 text-balance text-2xl font-medium leading-snug tracking-[-0.5px] text-foreground md:text-3xl">
              Menjadikan harga pangan{" "}
              <span className="font-serif-accent text-secondary">transparan dan dapat diprediksi</span>{" "}
              agar tekanan inflasi terbaca sebelum menjadi krisis.
            </p>
          </div>
        </div>
      </section>

      {/* What we do */}
      <section className="px-6 py-16 md:px-12 md:py-24">
        <div className="mx-auto max-w-6xl">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-balance text-3xl font-medium leading-tight tracking-[-1px] md:text-5xl">
              Apa yang kami <span className="font-serif-accent text-secondary">lakukan</span>
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
              Empat hal yang membedakan pemantauan kami dari dashboard angka biasa.
            </p>
          </div>
          <div className="mt-14 grid gap-4 md:grid-cols-2">
            {WHAT.map(({ Icon, title, copy }) => (
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

      {/* What makes us different */}
      <section className="px-6 py-16 md:px-12 md:py-24">
        <div className="mx-auto max-w-6xl">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-balance text-3xl font-medium leading-tight tracking-[-1px] md:text-5xl">
              Yang membuat kami <span className="font-serif-accent text-secondary">berbeda</span>
            </h2>
          </div>
          <div className="mt-14 grid gap-4 md:grid-cols-3">
            {DIFF.map(({ Icon, title, copy }) => (
              <div key={title} className="liquid-glass rounded-3xl p-7 transition hover:border-secondary/30">
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/15 text-primary">
                  <Icon className="h-5 w-5" />
                </span>
                <h3 className="mt-5 text-lg font-semibold text-foreground">{title}</h3>
                <p className="mt-2.5 text-sm leading-6 text-muted-foreground">{copy}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="px-6 py-16 md:px-12 md:py-24">
        <div className="mx-auto max-w-6xl">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-balance text-3xl font-medium leading-tight tracking-[-1px] md:text-5xl">
              Nilai yang kami <span className="font-serif-accent text-secondary">pegang</span>
            </h2>
          </div>
          <div className="mt-14 grid gap-4 md:grid-cols-3">
            {VALUES.map((v, i) => (
              <div key={v.title} className="liquid-glass rounded-3xl p-7">
                <span className="text-3xl font-bold text-secondary/40">0{i + 1}</span>
                <h3 className="mt-4 text-lg font-semibold text-foreground">{v.title}</h3>
                <p className="mt-2.5 text-sm leading-6 text-muted-foreground">{v.copy}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-20 md:px-12 md:py-28">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-balance text-3xl font-medium leading-tight tracking-[-1px] md:text-5xl">
            Ingin tahu lebih lanjut?
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-base leading-7 text-muted-foreground">
            Jelajahi dashboard publik, baca analisis harian, atau ajak kami berkolaborasi.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/login"
              className="inline-flex h-12 items-center justify-center rounded-full bg-secondary px-8 text-base font-semibold text-secondary-foreground transition hover:bg-secondary/90"
            >
              Buka Dashboard <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
            <Link
              href="/partner"
              className="inline-flex h-12 items-center justify-center rounded-full border border-white/15 bg-white/5 px-8 text-base font-medium text-foreground backdrop-blur transition hover:bg-white/10"
            >
              Jadi Mitra
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
