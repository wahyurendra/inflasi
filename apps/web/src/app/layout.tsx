import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/instrument-serif/400.css";
import "@fontsource/instrument-serif/400-italic.css";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

const siteUrl = process.env.NEXT_PUBLIC_APP_URL || "https://inflasi.id";

const description =
  "Platform intelijen inflasi pangan berbasis AI untuk Indonesia: pantau harga pangan harian, heatmap tekanan harga 38 provinsi, forecast multi-horizon, deteksi anomali, dan laporan harga crowdsourced.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Inflasi.id — Pemantauan & Prediksi Inflasi Pangan Indonesia",
    template: "%s · Inflasi.id",
  },
  description,
  applicationName: "Inflasi.id",
  keywords: [
    "inflasi pangan",
    "harga pangan Indonesia",
    "pemantauan harga pangan",
    "prediksi inflasi",
    "forecast inflasi pangan",
    "harga komoditas",
    "harga sembako",
    "heatmap harga pangan",
    "deteksi anomali harga",
    "ketahanan pangan",
    "early warning inflasi",
    "data harga pangan",
    "food inflation Indonesia",
    "food price intelligence",
  ],
  authors: [{ name: "Inflasi.id", url: siteUrl }],
  creator: "Inflasi.id",
  publisher: "Inflasi.id",
  category: "technology",
  formatDetection: { email: false, address: false, telephone: false },
  alternates: { canonical: "/" },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
      { url: "/favicon.ico", sizes: "any" },
    ],
    shortcut: "/favicon.ico",
    apple: "/logo.svg",
  },
  manifest: "/manifest.webmanifest",
  openGraph: {
    type: "website",
    locale: "id_ID",
    url: siteUrl,
    siteName: "Inflasi.id",
    title: "Inflasi.id — Pemantauan & Prediksi Inflasi Pangan Indonesia",
    description,
    images: [
      {
        url: `${siteUrl}/dashboard-heatmap.png`,
        width: 1806,
        height: 1012,
        alt: "Dashboard Peta Tekanan Harga Inflasi.id — heatmap nasional dan ranking provinsi",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Inflasi.id — Pemantauan & Prediksi Inflasi Pangan Indonesia",
    description,
    images: [`${siteUrl}/dashboard-heatmap.png`],
  },
};

export const viewport: Viewport = {
  themeColor: "#0e1512",
  colorScheme: "dark light",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
