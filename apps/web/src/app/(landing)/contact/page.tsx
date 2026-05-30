import type { Metadata } from "next";
import {
  Mail,
  Handshake,
  Newspaper,
  Code2,
  MessageCircle,
} from "lucide-react";
import { Navbar, Footer } from "@/components/landing/premium-landing";
import { ContactForm } from "@/components/landing/contact-form";

const siteUrl = process.env.NEXT_PUBLIC_APP_URL || "https://inflasi.id";

const description =
  "Hubungi tim inflasi.id untuk pertanyaan umum, akses data & API, dukungan teknis, atau peliputan media seputar pemantauan inflasi pangan Indonesia.";

export const metadata: Metadata = {
  title: "Kontak — Hubungi Tim Inflasi.id",
  description,
  alternates: { canonical: "/contact" },
  openGraph: {
    type: "website",
    url: `${siteUrl}/contact`,
    title: "Kontak — Inflasi.id",
    description,
  },
  twitter: {
    card: "summary_large_image",
    title: "Kontak — Inflasi.id",
    description,
  },
};

const CHANNELS = [
  {
    Icon: MessageCircle,
    title: "Pertanyaan umum",
    copy: "Pertanyaan seputar produk, data, atau cara kerja platform.",
    email: "hello@inflasi.id",
  },
  {
    Icon: Handshake,
    title: "Kemitraan",
    copy: "Pemerintah, institusi, dan organisasi yang ingin berkolaborasi.",
    email: "partnership@inflasi.id",
    href: "/partner",
  },
  {
    Icon: Code2,
    title: "Akses data & API",
    copy: "Permintaan akses dataset, dokumentasi, dan integrasi teknis.",
    email: "data@inflasi.id",
  },
  {
    Icon: Newspaper,
    title: "Media & pers",
    copy: "Peliputan, wawancara, dan permintaan data untuk jurnalisme.",
    email: "media@inflasi.id",
  },
];

export default function ContactPage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ContactPage",
    name: "Kontak — Inflasi.id",
    description,
    url: `${siteUrl}/contact`,
    inLanguage: "id-ID",
    publisher: {
      "@type": "Organization",
      name: "Inflasi.id",
      url: siteUrl,
      email: "hello@inflasi.id",
    },
  };

  return (
    <main className="landing-theme min-h-screen bg-background text-foreground">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <Navbar />

      {/* Hero */}
      <section className="relative overflow-hidden px-6 pb-12 pt-32 md:px-12 md:pt-40">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-[480px] bg-[radial-gradient(circle_at_50%_0%,hsl(var(--primary)/0.26),transparent_60%)]"
        />
        <div aria-hidden className="pointer-events-none absolute inset-0 opacity-40 landing-grain" />
        <div className="relative mx-auto max-w-3xl text-center">
          <p className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-secondary">
            <Mail className="h-3.5 w-3.5" />
            Kontak
          </p>
          <h1 className="text-balance text-4xl font-medium leading-[1.05] tracking-[-1.5px] md:text-6xl">
            Mari <span className="font-serif-accent text-secondary">terhubung</span>
          </h1>
          <p className="mx-auto mt-6 max-w-xl text-base leading-7 text-hero-subtitle opacity-90 md:text-lg">
            Punya pertanyaan, butuh akses data, atau ingin meliput? Tim kami siap membantu dan
            merespons dalam 2–3 hari kerja.
          </p>
        </div>
      </section>

      {/* Channels + Form */}
      <section className="px-6 py-16 md:px-12 md:py-20">
        <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          {/* Channels */}
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-foreground">Saluran kontak</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Pilih saluran yang sesuai, atau gunakan formulir di samping.
            </p>
            <div className="mt-8 space-y-3">
              {CHANNELS.map(({ Icon, title, copy, email, href }) => (
                <div key={title} className="liquid-glass flex items-start gap-4 rounded-2xl p-5">
                  <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-secondary/15 text-secondary">
                    <Icon className="h-5 w-5" />
                  </span>
                  <div className="min-w-0">
                    <h3 className="text-sm font-semibold text-foreground">{title}</h3>
                    <p className="mt-1 text-xs leading-5 text-muted-foreground">{copy}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1">
                      <a
                        href={`mailto:${email}`}
                        className="text-xs font-medium text-secondary hover:underline"
                      >
                        {email}
                      </a>
                      {href && (
                        <a href={href} className="text-xs text-muted-foreground hover:text-foreground">
                          Halaman kemitraan →
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Form */}
          <div>
            <h2 className="mb-6 text-2xl font-semibold tracking-tight text-foreground">
              Kirim pesan
            </h2>
            <ContactForm />
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
