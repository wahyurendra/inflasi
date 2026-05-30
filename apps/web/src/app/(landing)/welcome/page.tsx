import type { Metadata } from "next";
import PremiumLandingPage from "@/components/landing/premium-landing";

const siteUrl = process.env.NEXT_PUBLIC_APP_URL || "https://inflasi.id";

const description =
  "Inflasi.id membantu warga, pemerintah daerah, dan institusi keuangan memantau harga pangan, mendeteksi anomali, dan memprediksi tren inflasi di 38 provinsi menggunakan intelijen crowdsourced dan AI.";

const ogImage = {
  url: `${siteUrl}/dashboard-heatmap.png`,
  width: 1806,
  height: 1012,
  alt: "Dashboard Peta Tekanan Harga Inflasi.id — heatmap nasional dan ranking provinsi",
};

export const metadata: Metadata = {
  title: "Intelijen Inflasi Pangan Indonesia",
  description,
  alternates: { canonical: "/welcome" },
  // Note: Next.js shallow-merges openGraph/twitter — a child override replaces
  // the parent object wholesale, so image/card must be repeated here.
  openGraph: {
    type: "website",
    locale: "id_ID",
    siteName: "Inflasi.id",
    url: `${siteUrl}/welcome`,
    title: "Inflasi.id — Intelijen Inflasi Pangan Indonesia",
    description,
    images: [ogImage],
  },
  twitter: {
    card: "summary_large_image",
    title: "Inflasi.id — Intelijen Inflasi Pangan Indonesia",
    description,
    images: [`${siteUrl}/dashboard-heatmap.png`],
  },
};

// Structured data — helps search engines understand the org, the site search,
// and the software product for rich results.
const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${siteUrl}/#organization`,
      name: "Inflasi.id",
      url: siteUrl,
      logo: `${siteUrl}/logo.svg`,
      description,
      areaServed: { "@type": "Country", name: "Indonesia" },
    },
    {
      "@type": "WebSite",
      "@id": `${siteUrl}/#website`,
      url: siteUrl,
      name: "Inflasi.id",
      inLanguage: "id-ID",
      publisher: { "@id": `${siteUrl}/#organization` },
      potentialAction: {
        "@type": "SearchAction",
        target: {
          "@type": "EntryPoint",
          urlTemplate: `${siteUrl}/komoditas?q={search_term_string}`,
        },
        "query-input": "required name=search_term_string",
      },
    },
    {
      "@type": "WebApplication",
      name: "Inflasi.id",
      url: siteUrl,
      applicationCategory: "BusinessApplication",
      operatingSystem: "Web",
      inLanguage: "id-ID",
      description,
      offers: { "@type": "Offer", price: "0", priceCurrency: "IDR" },
      featureList: [
        "Heatmap tekanan harga pangan 38 provinsi",
        "Forecast inflasi multi-horizon berbasis AI",
        "Deteksi anomali harga real-time",
        "Laporan harga crowdsourced tervalidasi",
        "Ranking provinsi & komoditas",
      ],
    },
  ],
};

export default function LandingPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <PremiumLandingPage />
    </>
  );
}
